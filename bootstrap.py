#!/usr/bin/env python3
"""
BigQueryデータセット・テーブルおよびGCSバケットを作成するセットアップスクリプト。

冪等（何度実行しても安全）。既に存在するリソースはスキップする。

Usage:
    python bootstrap.py
    python bootstrap.py --dataset rakuten_orders_shopB   # データセット名を上書き
    python bootstrap.py --skip-bucket                    # GCSバケット作成をスキップ
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from google.cloud import bigquery, storage
from google.api_core.exceptions import Conflict

from config import PROJECT_ID, BQ_DATASET, BQ_LOCATION, BUCKET_NAME

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

SCHEMA_DIR = Path(__file__).parent / "schema"

# スキーマファイル名とBQテーブル名の対応（順序は依存関係に合わせる）
TABLE_SCHEMAS = [
    ("orders",                              "orders.json"),
    ("order_items",                         "order_items.json"),
    ("product_master_raw",                  "product_master_raw.json"),
    ("user_first_purchase_info",            "user_first_purchase_info.json"),
    ("entry_product_ltv_by_month_offset",   "entry_product_ltv_by_month_offset.json"),
]


def _load_schema(filename: str):
    """schema/*.json を読み込み、(fields, time_partitioning, clustering_fields) を返す"""
    raw = json.loads((SCHEMA_DIR / filename).read_text(encoding="utf-8"))
    fields = [bigquery.SchemaField.from_api_repr(f) for f in raw["fields"]]

    tp = None
    if tp_cfg := raw.get("time_partitioning"):
        tp = bigquery.TimePartitioning(
            field=tp_cfg["field"],
            type_=tp_cfg["type"],
        )

    clustering = raw.get("clustering_fields")
    return fields, tp, clustering


def create_dataset(client: bigquery.Client, dataset_id: str) -> None:
    """データセットを作成する。既に存在する場合はスキップ。"""
    full_id = f"{client.project}.{dataset_id}"
    dataset = bigquery.Dataset(full_id)
    dataset.location = BQ_LOCATION

    try:
        client.create_dataset(dataset, exists_ok=False)
        log.info(f"Created dataset: {full_id}")
    except Conflict:
        log.info(f"Dataset already exists (skip): {full_id}")


def create_table(client: bigquery.Client, dataset_id: str, table_name: str, schema_file: str) -> None:
    """テーブルを作成する。既に存在する場合はスキップ。"""
    full_id = f"{client.project}.{dataset_id}.{table_name}"
    fields, tp, clustering = _load_schema(schema_file)

    table = bigquery.Table(full_id, schema=fields)
    if tp:
        table.time_partitioning = tp
    if clustering:
        table.clustering_fields = clustering

    try:
        client.create_table(table, exists_ok=False)
        suffix = ""
        if tp:
            suffix += f" [PARTITION BY {tp.field}]"
        if clustering:
            suffix += f" [CLUSTER BY {', '.join(clustering)}]"
        log.info(f"Created table: {full_id}{suffix}")
    except Conflict:
        log.info(f"Table already exists (skip): {full_id}")


def create_bucket(bucket_name: str) -> None:
    """GCSバケットを作成する。既に存在する場合はスキップ。"""
    client = storage.Client(project=PROJECT_ID)
    bucket = storage.Bucket(client, bucket_name)
    bucket.location = BQ_LOCATION  # BQと同一リージョンに揃える

    try:
        client.create_bucket(bucket)
        log.info(f"Created GCS bucket: gs://{bucket_name}")
    except Conflict:
        log.info(f"GCS bucket already exists (skip): gs://{bucket_name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="BigQueryとGCSのリソースをセットアップします。")
    parser.add_argument("--dataset",      default=None, help=f"BQデータセット名（デフォルト: {BQ_DATASET}）")
    parser.add_argument("--skip-bucket",  action="store_true", help="GCSバケットの作成をスキップする")
    args = parser.parse_args()

    dataset_id = args.dataset or BQ_DATASET

    if not PROJECT_ID:
        log.error("PROJECT_ID が設定されていません。環境変数または .env ファイルで設定してください。")
        sys.exit(1)

    log.info(f"Project  : {PROJECT_ID}")
    log.info(f"Dataset  : {dataset_id}")
    log.info(f"Location : {BQ_LOCATION}")
    if not args.skip_bucket:
        log.info(f"Bucket   : {BUCKET_NAME or '(未設定 - スキップ)'}")
    log.info("")

    bq_client = bigquery.Client(project=PROJECT_ID, location=BQ_LOCATION)

    # 1) データセット作成
    create_dataset(bq_client, dataset_id)

    # 2) テーブル作成
    for table_name, schema_file in TABLE_SCHEMAS:
        create_table(bq_client, dataset_id, table_name, schema_file)

    # 3) GCSバケット作成
    if not args.skip_bucket:
        if BUCKET_NAME:
            create_bucket(BUCKET_NAME)
        else:
            log.warning("BUCKET_NAME が設定されていないため、GCSバケットの作成をスキップします。")

    log.info("")
    log.info("セットアップ完了。")


if __name__ == "__main__":
    main()
