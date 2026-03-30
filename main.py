import json
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
from dateutil.relativedelta import relativedelta
from flask import jsonify

from config import (
    BQ_DATASET,
    BQ_TABLE_ORDERS,
    BQ_TABLE_ORDER_ITEMS,
    STRICT_RAW_PER_BATCH,
    SKIP_LTV_UPDATE,
)
from utils import setup_cloud_logging
from rakuten_client import search_order, get_order, PAGE_SIZE
from storage_client import (
    upload_raw_json,
    acquire_monthly_lock,
    complete_monthly_lock,
    release_monthly_lock,
)

SEARCH_ORDER_CHUNK_DAYS = 7  # searchOrder は 15,000 件/呼び出しのハードリミットがあるため
                              # 週単位に分割して呼び出し、1 回あたりの件数を上限以内に抑える
from transform import normalize_all
from product_master_sync import sync_product_master
from bigquery_client import (
    replace_month_with_dataframes,
    delete_between,
    insert_dataframe,
)

JST = ZoneInfo("Asia/Tokyo")


# =========================
# 日付ユーティリティ
# =========================
def month_start(dt: datetime) -> datetime:
    """dt（JST）の月初 00:00:00 JST を返す"""
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def next_month(dt: datetime) -> datetime:
    return month_start(dt) + relativedelta(months=1)


def prev_month(dt: datetime) -> datetime:
    return month_start(dt) - relativedelta(months=1)


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
    """JST aware datetime を ISO8601 文字列へ（オフセット含む, コロンなし）"""
    return dt.strftime("%Y-%m-%dT%H:%M:%S%z")


# =========================
# 期間決定（モード）
# =========================
def resolve_ranges_from_request(req):
    """
    mode:
      - MONTHLY（デフォルト）: 前月 00:00:00 ～ 当月 00:00:00（JST）
      - HISTORICAL: 今日から730日前までを月単位で分割
      - CUSTOM: ?start=YYYY-MM-DD&end=YYYY-MM-DD（JST解釈、endは翌日0時未満開区間）
    戻り値: [(m_start_jst, m_end_jst), ...] JST aware datetimes のリスト
    """
    args = req.args or {}
    mode = (args.get("mode") or "MONTHLY").upper()

    now_jst = datetime.now(JST)

    if mode == "HISTORICAL":
        end_jst = now_jst
        start_jst = now_jst - timedelta(days=730)
        # 月境界に合わせて分割
        ranges = list(monthly_ranges_jst(start_jst, end_jst))

    elif mode == "CUSTOM":
        # 例: ?mode=CUSTOM&start=2025-01-01&end=2025-03-31
        start_s = args.get("start")
        end_s = args.get("end")
        if not start_s or not end_s:
            raise ValueError(
                "CUSTOMモードでは ?start=YYYY-MM-DD & ?end=YYYY-MM-DD が必須です。"
            )
        start_jst = datetime.strptime(start_s, "%Y-%m-%d").replace(tzinfo=JST)
        # end は最終日の 23:59:59 までを含めたいので、翌日0時を開区間とする
        end_jst = (datetime.strptime(end_s, "%Y-%m-%d") + timedelta(days=1)).replace(
            tzinfo=JST, hour=0, minute=0, second=0, microsecond=0
        )
        ranges = list(monthly_ranges_jst(start_jst, end_jst))

    else:
        # MONTHLY: 前月分
        cur_month_start = month_start(now_jst)
        prev_start = prev_month(now_jst)  # 前月の月初
        ranges = [(prev_start, cur_month_start)]

    return mode, ranges


# =========================
# searchOrder 週分割ラッパー
# =========================
def _search_order_chunked(start_jst: datetime, end_jst: datetime) -> list:
    """
    searchOrder の 15,000 件/呼び出しハードリミットを回避するため、
    期間を SEARCH_ORDER_CHUNK_DAYS 日単位に分割して呼び出し、結果を結合して返す。
    重複排除は順序を保って行う。
    """
    all_orders = []
    seen: set = set()
    chunk_start = start_jst

    while chunk_start < end_jst:
        chunk_end = min(chunk_start + timedelta(days=SEARCH_ORDER_CHUNK_DAYS), end_jst)
        chunk_orders = search_order(iso_jst(chunk_start), iso_jst(chunk_end))
        for o in chunk_orders:
            if o not in seen:
                seen.add(o)
                all_orders.append(o)
        logging.info(
            f"  chunk {iso_jst(chunk_start)}〜{iso_jst(chunk_end)}: "
            f"{len(chunk_orders)} 件 (累計 {len(all_orders)} 件)"
        )
        chunk_start = chunk_end

    return all_orders


# =========================
# コア処理（1か月分）
# =========================
def process_one_month(m_start_jst: datetime, m_end_jst: datetime) -> dict:
    """
    1か月（[m_start_jst, m_end_jst)）分の注文を取得→保存→正規化→BQ反映
    """
    start_iso = iso_jst(m_start_jst)
    end_iso = iso_jst(m_end_jst)
    # BQはタイムゾーンオフセットのコロン付き書式を好むため変換しておく
    def _bq_iso(s: str) -> str:
        return f"{s[:-2]}:{s[-2:]}" if s and len(s) >= 5 and s[-3] != ":" else s

    start_iso_bq = _bq_iso(start_iso)
    end_iso_bq = _bq_iso(end_iso)

    logging.info(f"=== Month range (JST): {start_iso} 〜 {end_iso} ===")

    # 1) 注文番号一覧を取得（searchOrder・週分割）
    # searchOrder は 15,000 件/呼び出しのハードリミットがあるため週単位で分割して呼ぶ
    order_numbers = _search_order_chunked(m_start_jst, m_end_jst)
    total_numbers = len(order_numbers)
    if total_numbers == 0:
        logging.error(
            "searchOrderが0件（APIエラーの可能性あり）のため、この月のBQ更新をスキップします"
        )
        return {
            "range": [start_iso, end_iso],
            "order_numbers": 0,
            "orders_rows": 0,
            "order_items_rows": 0,
            "note": "searchOrder_empty_skip",
        }
    logging.info(f"searchOrder: {total_numbers} order_numbers")

    # 2) 注文詳細を取得（getOrder）＆Raw保存
    #    デフォルトは「結合した1つのJSON」を保存。STRICT_RAW_PER_BATCH=True ならAPIバッチごと保存。
    all_order_models = []

    if STRICT_RAW_PER_BATCH:
        # 自分でバッチ分割して getOrder を呼び出し、各レスポンスをRaw保存
        for i in range(0, total_numbers, PAGE_SIZE):
            batch = order_numbers[i : i + PAGE_SIZE]
            batch_models = get_order(batch)  # 返り値は OrderModelList の配列
            # Raw保存（APIレスポンスと同等の構造に揃える）
            if batch_models:
                upload_raw_json(
                    data={"OrderModelList": batch_models, "version": 9},
                    prefix="raw",
                    batch_id=f"{m_start_jst.strftime('%Y-%m')}-batch{(i//PAGE_SIZE)+1}",
                )
                all_order_models.extend(batch_models)
    else:
        # 一括で詳細取得 → 1ファイルに保存
        all_order_models = get_order(order_numbers)
        upload_raw_json(
            data={"OrderModelList": all_order_models, "version": 9},
            prefix="raw",
            batch_id=m_start_jst.strftime("%Y-%m"),
        )

    # 3) 正規化（orders / order_items）
    getorder_json = {"OrderModelList": all_order_models}
    orders_df, order_items_df = normalize_all(getorder_json)

    # order_items にも購入日時列を持たせ、親注文の order_datetime をコピーする
    if order_items_df is not None and not order_items_df.empty:
        order_datetime_map = orders_df.set_index("order_number")["order_datetime"] if orders_df is not None else {}
        order_items_df["order_datetime"] = order_items_df["order_number"].map(order_datetime_map)

    # 4) BigQuery 反映（該当月は完全更新：削除→挿入）
    #    order_items も order_datetime を持たせたので、同列を基準に削除
    replace_month_with_dataframes(
        orders_df=orders_df,
        order_items_df=order_items_df,
        orders_table=f"{BQ_DATASET}.{BQ_TABLE_ORDERS}",
        items_table=f"{BQ_DATASET}.{BQ_TABLE_ORDER_ITEMS}",
        ts_column_orders="order_datetime",
        ts_column_items="order_datetime",
        month_start_iso=start_iso_bq,
        month_end_iso=end_iso_bq,
    )
    
    # 5) 初回購入情報テーブル更新（エラーハンドリング）
    first_purchase_result = None
    try:
        from ltv_updater import update_user_first_purchase_info
        first_purchase_result = update_user_first_purchase_info(m_start_jst)
        logging.info(f"初回購入情報更新成功: {first_purchase_result}")
    except Exception as e:
        logging.error(f"初回購入情報更新失敗（注文取り込みは成功）: {e}", exc_info=True)
    
    # 6) LTV集計テーブル更新（エラーハンドリング）
    ltv_result = None
    if not SKIP_LTV_UPDATE:
        try:
            from ltv_updater import update_entry_product_ltv
            ltv_result = update_entry_product_ltv(m_start_jst)
            logging.info("LTVテーブル更新成功")
        except Exception as e:
            logging.error(f"LTVテーブル更新失敗（注文取り込みは成功）: {e}", exc_info=True)
    else:
        logging.info("LTVテーブル更新をスキップ（SKIP_LTV_UPDATE=true）")

    return {
        "range": [start_iso, end_iso],
        "order_numbers": total_numbers,
        "orders_rows": 0 if orders_df is None or orders_df.empty else len(orders_df),
        "order_items_rows": (
            0 if order_items_df is None or order_items_df.empty else len(order_items_df)
        ),
        "first_purchase_update": first_purchase_result,
        "ltv_update": ltv_result,
    }


# =========================
# Cloud Function エントリーポイント
# =========================
def main_endpoint(request):
    """
    月次更新エンドポイント（既存）
    
    HTTP Trigger:
      - ?mode=MONTHLY（既定）, HISTORICAL, CUSTOM
      - CUSTOM の場合: ?start=YYYY-MM-DD&end=YYYY-MM-DD （JSTで解釈）
      - ?dry_run=1 で検索のみ（GCS/BQ書き込みをスキップ）
    """
    try:
        # Cloud Loggingの設定
        setup_cloud_logging()

        mode, ranges = resolve_ranges_from_request(request)
        args = request.args or {}
        dry_run = (args.get("dry_run") or "0") in ("1", "true", "t", "yes", "y")

        summary = {
            "mode": mode,
            "ranges_count": len(ranges),
            "details": [],
            "dry_run": dry_run,
        }

        if not dry_run:
            summary["master_sync"] = sync_product_master()

        for m_start, m_end in ranges:
            start_iso = iso_jst(m_start)
            end_iso = iso_jst(m_end)
            year_month = m_start.strftime("%Y-%m")

            if dry_run:
                # 取得件数だけ見たい場合（週分割 searchOrder 呼んで終了）
                order_numbers = _search_order_chunked(m_start, m_end)
                summary["details"].append(
                    {
                        "range": [start_iso, end_iso],
                        "order_numbers": len(order_numbers),
                        "orders_rows": None,
                        "order_items_rows": None,
                        "note": "dry_run",
                    }
                )
                continue

            # MONTHLY モードのみ GCS ロックで重複実行を防ぐ
            # CUSTOM / HISTORICAL は手動実行なのでロック不要
            if mode == "MONTHLY":
                if not acquire_monthly_lock(year_month):
                    summary["details"].append(
                        {
                            "range": [start_iso, end_iso],
                            "note": "skipped_already_locked",
                        }
                    )
                    continue

            # 本処理
            try:
                detail = process_one_month(m_start, m_end)
                if mode == "MONTHLY":
                    complete_monthly_lock(year_month)
            except Exception as month_err:
                if mode == "MONTHLY":
                    # ロックを解放して手動リトライを可能にする
                    release_monthly_lock(year_month)
                raise month_err
            summary["details"].append(detail)

        return jsonify({"status": "success", **summary})

    except Exception as e:
        logging.exception("ETL failed")
        return jsonify({"status": "error", "message": str(e)}), 500


def sync_product_master_endpoint(request):
    """
    商品マスタ同期＋LTV商品名更新エンドポイント（新規）
    
    Googleスプレッドシートで商品名を変更した後に呼び出す。
    - product_master_raw を最新に更新
    - entry_product_ltv_by_month_offset の商品名を更新
    
    user_first_purchase_info は次回の月次更新時に自動的に同期される。
    """
    try:
        # Cloud Loggingの設定
        setup_cloud_logging()
        
        logging.info("Starting product master sync...")
        
        # 1. 商品マスタ同期
        master_result = sync_product_master()
        logging.info(f"Product master synced: {master_result}")
        
        # 2. LTVテーブルの商品名を更新
        logging.info("Starting LTV item names update...")
        from ltv_updater import update_ltv_item_names_from_master
        ltv_result = update_ltv_item_names_from_master()
        logging.info(f"LTV item names updated: {ltv_result}")
        
        return jsonify({
            "status": "success",
            "master_sync": master_result,
            "ltv_names_updated": ltv_result,
            "timestamp": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
            "note": "user_first_purchase_info will be synced at next monthly batch"
        }), 200
        
    except Exception as e:
        logging.exception("Failed to sync product master")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat()
        }), 500


# admin エントリーポイントを main.py から公開（Functions Framework は main.py から関数を探す）
from admin import admin  # noqa: F401


# Cloud Functions の場合、main という名前でエクスポート
def main(request):
    """
    Cloud Functions (gen2) entry point.
    Dispatch by path so / and /sync-product-master both work without Flask app routing.
    """
    path = (request.path or "/").rstrip("/") or "/"
    if path == "/sync-product-master":
        return sync_product_master_endpoint(request)
    return main_endpoint(request)
