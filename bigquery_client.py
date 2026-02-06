import os
import uuid
import logging
from typing import List, Optional, Sequence

import pandas as pd
from google.cloud import bigquery

PROJECT_ID = os.getenv("PROJECT_ID")
# データセットのロケーションに合わせる（例: asia-northeast1）
BQ_LOCATION = os.getenv("BQ_LOCATION", None)  # 未指定なら自動解決


# ------------------------------------------------------------
# 基本: クライアント生成 / テーブルIDユーティリティ
# ------------------------------------------------------------
def _client(project_id: Optional[str] = None) -> bigquery.Client:
    return bigquery.Client(project=project_id or PROJECT_ID)

def _qualify(table_id: str) -> str:
    """`project.dataset.table` 形式に整える（project 省略時は環境PROJECT_IDを使用）"""
    if table_id.count(".") == 1:
        return f"{PROJECT_ID}.{table_id}"
    return table_id

def _bq_ref(table_id: str) -> bigquery.TableReference:
    client = _client()
    project, dataset, table = _qualify(table_id).split(".")
    return bigquery.TableReference(bigquery.DatasetReference(project, dataset), table)


# ------------------------------------------------------------
# 1) DataFrame をストリーミング（LoadJob）で投入
# ------------------------------------------------------------
def insert_dataframe(
    df: pd.DataFrame,
    table_id: str,
    write_disposition: str = "WRITE_APPEND",
    ignore_if_empty: bool = True,
    job_labels: Optional[dict] = None,
) -> bigquery.LoadJob:
    """
    DataFrame → BigQuery へ投入（最も手軽な方法）
    - write_disposition: WRITE_APPEND / WRITE_TRUNCATE / WRITE_EMPTY
    """
    if df is None or df.empty:
        if ignore_if_empty:
            logging.info(f"[BQ] Skip insert: empty DataFrame for {table_id}")
            return None
        raise ValueError("DataFrame is empty")

    table_ref = _bq_ref(table_id)
    client = _client()

    job_config = bigquery.LoadJobConfig(
        write_disposition=write_disposition,
    )
    # PyAPI: pyarrow が必要（requirements.txt に `pyarrow` を追加）
    job = client.load_table_from_dataframe(
        df, destination=table_ref, job_config=job_config, job_id_prefix="df_load_", project=table_ref.project, location=BQ_LOCATION
    )

    logging.info(f"[BQ] Loading {len(df)} rows into {table_ref.path}")
    result = job.result()
    logging.info(f"[BQ] Load done: output_rows={result.output_rows}")
    return result


# ------------------------------------------------------------
# 2) GCS 上のファイルをロード（大量データ向け）
# ------------------------------------------------------------
def load_from_gcs(
    gcs_uri: str,
    table_id: str,
    source_format: str = "NEWLINE_DELIMITED_JSON",  # "CSV" も可
    write_disposition: str = "WRITE_APPEND",
    autodetect: bool = True,
    schema: Optional[Sequence[bigquery.SchemaField]] = None,
    field_delimiter: str = ",",
    skip_leading_rows: int = 0,
) -> bigquery.LoadJob:
    """
    GCS → BigQuery ロード
    - NDJSON or CSV を想定
    """
    client = _client()
    table_ref = _bq_ref(table_id)

    job_config = bigquery.LoadJobConfig(
        source_format=source_format,
        write_disposition=write_disposition,
        autodetect=autodetect if schema is None else False,
        schema=schema,
        field_delimiter=field_delimiter,
        skip_leading_rows=skip_leading_rows,
    )

    logging.info(f"[BQ] Load from GCS {gcs_uri} -> {table_ref.path}")
    job = client.load_table_from_uri(gcs_uri, table_ref, job_config=job_config, job_id_prefix="gcs_load_", location=BQ_LOCATION)
    result = job.result()
    logging.info(f"[BQ] Load done: output_rows={result.output_rows}")
    return result


# ------------------------------------------------------------
# 3) 月次の完全更新（該当月を削除 → 再挿入）
#    JST基準での月境界にこだわる場合は start/end を明示で渡す
# ------------------------------------------------------------
def delete_between(
    table_id: str,
    ts_column: str,
    start_ts_iso: str,  # 例: "2025-10-01T00:00:00+09:00"
    end_ts_iso: str,    # 例: "2025-11-01T00:00:00+09:00"
) -> bigquery.QueryJob:
    """
    指定のタイムスタンプ列で [start, end) を削除
    ※ タイムゾーン付きISO文字列推奨
    """
    client = _client()
    full = _qualify(table_id)
    sql = f"""
    DELETE FROM `{full}`
    WHERE {ts_column} >= TIMESTAMP(@start_ts)
      AND {ts_column} <  TIMESTAMP(@end_ts)
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_ts", "STRING", start_ts_iso),
            bigquery.ScalarQueryParameter("end_ts", "STRING", end_ts_iso),
        ]
    )
    logging.info(f"[BQ] DELETE BETWEEN on {full}: {start_ts_iso} - {end_ts_iso}")
    job = client.query(sql, job_config=job_config, location=BQ_LOCATION)
    res = job.result()
    logging.info("[BQ] DELETE completed")
    return res


# ------------------------------------------------------------
# 4) 汎用 MERGE（UPSERT）
#    - df を一時テーブルにロード → キーで MERGE
# ------------------------------------------------------------
def upsert_by_keys(
    df: pd.DataFrame,
    target_table: str,
    key_columns: List[str],
    temp_table: Optional[str] = None,
    chunked_load: bool = False,
) -> None:
    """
    DataFrame を一時テーブルにロードし、キーで MERGE（UPSERT）
    - key_columns: ["order_number"] 等
    - temp_table: 明示しない場合は自動生成
    """
    if df is None or df.empty:
        logging.info(f"[BQ] Skip MERGE (empty df) for {target_table}")
        return

    client = _client()
    target_full = _qualify(target_table)
    project, dataset, _ = target_full.split(".")
    dataset_ref = bigquery.DatasetReference(project, dataset)

    # 一時テーブル名を生成
    tmp_name = temp_table or f"tmp_{uuid.uuid4().hex[:8]}"
    tmp_ref = bigquery.TableReference(dataset_ref, tmp_name)

    # 1) 一時テーブルへロード（テーブル作成 → 書き込み）
    logging.info(f"[BQ] Create temp table: {project}.{dataset}.{tmp_name}")
    job = client.load_table_from_dataframe(df, tmp_ref, job_id_prefix="tmp_df_", location=BQ_LOCATION)
    job.result()

    # 2) MERGE SQL を生成
    # すべてのカラム名
    cols = [field.name for field in client.get_table(tmp_ref).schema]
    # キー以外の更新対象列
    update_cols = [c for c in cols if c not in key_columns]

    on_clause = " AND ".join([f"T.{k} = S.{k}" for k in key_columns])
    set_clause = ", ".join([f"{c}=S.{c}" for c in update_cols])
    insert_cols = ", ".join(cols)
    insert_vals = ", ".join([f"S.{c}" for c in cols])

    sql = f"""
    MERGE `{target_full}` AS T
    USING `{project}.{dataset}.{tmp_name}` AS S
    ON {on_clause}
    WHEN MATCHED THEN UPDATE SET {set_clause}
    WHEN NOT MATCHED THEN INSERT ({insert_cols}) VALUES ({insert_vals})
    """

    logging.info(f"[BQ] MERGE into {target_full} on {key_columns}")
    qjob = client.query(sql, location=BQ_LOCATION)
    qjob.result()

    # 3) 後始末：一時テーブル削除
    logging.info(f"[BQ] Drop temp table: {project}.{dataset}.{tmp_name}")
    client.delete_table(tmp_ref, not_found_ok=True)


# ------------------------------------------------------------
# 5) 便利ラッパー: 月次完全更新（削除→挿入）
# ------------------------------------------------------------
def replace_month_with_dataframes(
    orders_df: pd.DataFrame,
    order_items_df: pd.DataFrame,
    orders_table: str,
    items_table: str,
    ts_column_orders: str,
    ts_column_items: str,
    month_start_iso: str,   # 例 "2025-10-01T00:00:00+09:00"
    month_end_iso: str,     # 例 "2025-11-01T00:00:00+09:00"
) -> None:
    """
    指定月を削除し、DataFrameを挿入する高水準ヘルパー
    - JSTの月境界で渡せば、そのまま期待通りに動作
    """
    # 1) 削除
    delete_between(orders_table, ts_column_orders, month_start_iso, month_end_iso)
    delete_between(items_table, ts_column_items, month_start_iso, month_end_iso)
    # 2) 挿入
    insert_dataframe(orders_df, orders_table, write_disposition="WRITE_APPEND")
    insert_dataframe(order_items_df, items_table, write_disposition="WRITE_APPEND")
    logging.info("[BQ] Monthly replace completed")
