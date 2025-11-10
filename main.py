import os
import json
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
from dateutil.relativedelta import relativedelta
from flask import jsonify

from utils import setup_cloud_logging
from rakuten_client import search_order, get_order, PAGE_SIZE  # 既存のひな型を利用
from storage_client import upload_raw_json
from transform import normalize_all
from bigquery_client import replace_month_with_dataframes, delete_between, insert_dataframe

# =========================
# 環境変数
# =========================
PROJECT_ID = os.getenv("PROJECT_ID")
BQ_DATASET = os.getenv("BQ_DATASET", "rakuten_orders")
BQ_TABLE_ORDERS = os.getenv("BQ_TABLE_ORDERS", "orders")
BQ_TABLE_ORDER_ITEMS = os.getenv("BQ_TABLE_ORDER_ITEMS", "order_items")
BUCKET_NAME = os.getenv("BUCKET_NAME")  # storage_client側で参照
BQ_LOCATION = os.getenv("BQ_LOCATION")  # 任意
# 厳密に「API呼び出し単位のRaw」を残したい場合は True
STRICT_RAW_PER_BATCH = os.getenv("STRICT_RAW_PER_BATCH", "false").lower() in ("true", "1", "t", "yes", "y")

JST = ZoneInfo("Asia/Tokyo")


# =========================
# 日付ユーティリティ
# =========================
def month_start(dt: datetime) -> datetime:
    """dt（JST）の月初 00:00:00 JST を返す"""
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

def next_month(dt: datetime) -> datetime:
    return (month_start(dt) + relativedelta(months=1))

def prev_month(dt: datetime) -> datetime:
    return (month_start(dt) - relativedelta(months=1))

def monthly_ranges_jst(start_dt: datetime, end_dt: datetime):
    """
    [start_dt, end_dt) をJSTの月境界で分割して yield (m_start, m_end)
    start_dt, end_dt は JST の aware datetime（end は開区間）
    """
    cur = month_start(start_dt)
    if cur < start_dt:
        # start_dtが月途中なら、その月初から
        cur = month_start(start_dt)
    while cur < end_dt:
        m_start = cur
        m_end = next_month(cur)
        if m_end > end_dt:
            m_end = end_dt
        yield (m_start, m_end)
        cur = next_month(cur)

def iso_jst(dt: datetime) -> str:
    """JST aware datetime を ISO8601 文字列へ（オフセット含む）"""
    return dt.isoformat(timespec="seconds")


# =========================
# 期間決定（モード）
# =========================
def resolve_ranges_from_request(request):
    """
    mode:
      - MONTHLY（デフォルト）: 前月 00:00:00 ～ 当月 00:00:00（JST）
      - HISTORICAL: 今日から730日前までを月単位で分割
      - CUSTOM: ?start=YYYY-MM-DD&end=YYYY-MM-DD（JST解釈、endは翌日0時未満開区間）
    戻り値: [(m_start_jst, m_end_jst), ...] JST aware datetimes のリスト
    """
    args = getattr(request, "args", {}) or {}
    mode = (args.get("mode") or "MONTHLY").upper()

    now_jst = datetime.now(JST)

    if mode == "HISTORICAL":
        end_jst = now_jst
        start_jst = (now_jst - timedelta(days=730))
        # 月境界に合わせて分割
        ranges = list(monthly_ranges_jst(start_jst, end_jst))

    elif mode == "CUSTOM":
        # 例: ?mode=CUSTOM&start=2025-01-01&end=2025-03-31
        start_s = args.get("start")
        end_s = args.get("end")
        if not start_s or not end_s:
            raise ValueError("CUSTOMモードでは ?start=YYYY-MM-DD & ?end=YYYY-MM-DD が必須です。")
        start_jst = datetime.strptime(start_s, "%Y-%m-%d").replace(tzinfo=JST)
        # end は最終日の 23:59:59 までを含めたいので、翌日0時を開区間とする
        end_jst = (datetime.strptime(end_s, "%Y-%m-%d") + timedelta(days=1)).replace(tzinfo=JST, hour=0, minute=0, second=0, microsecond=0)
        ranges = list(monthly_ranges_jst(start_jst, end_jst))

    else:
        # MONTHLY: 前月分
        cur_month_start = month_start(now_jst)
        prev_start = prev_month(now_jst)  # 前月の月初
        ranges = [(prev_start, cur_month_start)]

    return mode, ranges


# =========================
# コア処理（1か月分）
# =========================
def process_one_month(m_start_jst: datetime, m_end_jst: datetime) -> dict:
    """
    1か月（[m_start_jst, m_end_jst)）分の注文を取得→保存→正規化→BQ反映
    """
    start_iso = iso_jst(m_start_jst)
    end_iso = iso_jst(m_end_jst)

    logging.info(f"=== Month range (JST): {start_iso} 〜 {end_iso} ===")

    # 1) 注文番号一覧を取得（searchOrder）
    order_numbers = search_order(start_iso, end_iso)
    total_numbers = len(order_numbers)
    logging.info(f"searchOrder: {total_numbers} order_numbers")

    # 2) 注文詳細を取得（getOrder）＆Raw保存
    #    デフォルトは「結合した1つのJSON」を保存。STRICT_RAW_PER_BATCH=True ならAPIバッチごと保存。
    all_order_models = []

    if STRICT_RAW_PER_BATCH:
        # 自分でバッチ分割して getOrder を呼び出し、各レスポンスをRaw保存
        for i in range(0, total_numbers, PAGE_SIZE):
            batch = order_numbers[i:i + PAGE_SIZE]
            batch_models = get_order(batch)  # 返り値は OrderModelList の配列
            # Raw保存（APIレスポンスと同等の構造に揃える）
            if batch_models:
                upload_raw_json(
                    data={"OrderModelList": batch_models, "version": 9},
                    prefix="raw",
                    batch_id=f"{m_start_jst.strftime('%Y-%m')}-batch{(i//PAGE_SIZE)+1}"
                )
                all_order_models.extend(batch_models)
    else:
        # 一括で詳細取得 → 1ファイルに保存
        all_order_models = get_order(order_numbers)
        upload_raw_json(
            data={"OrderModelList": all_order_models, "version": 9},
            prefix="raw",
            batch_id=m_start_jst.strftime("%Y-%m")
        )

    # 3) 正規化（orders / order_items）
    getorder_json = {"OrderModelList": all_order_models}
    orders_df, order_items_df = normalize_all(getorder_json)

    # 4) BigQuery 反映（該当月は完全更新：削除→挿入）
    #    アイテム側に厳密な購入日時列がない場合は inserted_at を基準にして削除
    replace_month_with_dataframes(
        orders_df=orders_df,
        order_items_df=order_items_df,
        orders_table=f"{BQ_DATASET}.{BQ_TABLE_ORDERS}",
        items_table=f"{BQ_DATASET}.{BQ_TABLE_ORDER_ITEMS}",
        ts_column_orders="order_datetime",
        ts_column_items="inserted_at",
        month_start_iso=start_iso,
        month_end_iso=end_iso,
    )

    return {
        "range": [start_iso, end_iso],
        "order_numbers": total_numbers,
        "orders_rows": 0 if orders_df is None or orders_df.empty else len(orders_df),
        "order_items_rows": 0 if order_items_df is None or order_items_df.empty else len(order_items_df),
    }


# =========================
# Cloud Function エントリーポイント
# =========================
def main(request):
    """
    HTTP Trigger:
      - ?mode=MONTHLY（既定）, HISTORICAL, CUSTOM
      - CUSTOM の場合: ?start=YYYY-MM-DD&end=YYYY-MM-DD （JSTで解釈）
      - ?dry_run=1 で検索のみ（GCS/BQ書き込みをスキップ）
    """
    try:
        # Cloud Loggingの設定
        setup_cloud_logging()

        mode, ranges = resolve_ranges_from_request(request)
        args = getattr(request, "args", {}) or {}
        dry_run = (args.get("dry_run") or "0") in ("1", "true", "t", "yes", "y")

        summary = {
            "mode": mode,
            "ranges_count": len(ranges),
            "details": [],
            "dry_run": dry_run,
        }

        for (m_start, m_end) in ranges:
            start_iso = iso_jst(m_start)
            end_iso = iso_jst(m_end)

            if dry_run:
                # 取得件数だけ見たい場合（searchOrder呼んで終了）
                order_numbers = search_order(start_iso, end_iso)
                summary["details"].append({
                    "range": [start_iso, end_iso],
                    "order_numbers": len(order_numbers),
                    "orders_rows": None,
                    "order_items_rows": None,
                    "note": "dry_run",
                })
                continue

            # 本処理
            detail = process_one_month(m_start, m_end)
            summary["details"].append(detail)

        return jsonify({"status": "success", **summary})

    except Exception as e:
        logging.exception("ETL failed")
        return jsonify({"status": "error", "message": str(e)}), 500
