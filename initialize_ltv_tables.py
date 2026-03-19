#!/usr/bin/env python3
"""
初回購入情報テーブルとLTVテーブルの初期データ投入スクリプト

Usage:
    python initialize_ltv_tables.py
"""
import logging
from google.cloud import bigquery
from config import PROJECT_ID, BQ_DATASET
from ltv_updater import get_client

# Setup logging
logging.basicConfig(level=logging.INFO)


def initialize_user_first_purchase_info():
    """初回購入情報テーブルに全期間のデータを投入"""
    client = get_client()
    
    sql = f"""
    INSERT INTO `{PROJECT_ID}.{BQ_DATASET}.user_first_purchase_info`
    (user_email, first_order_number, first_order_date, first_order_month, 
     entry_manage_number, entry_item_name, updated_at)
    WITH product_master AS (
      SELECT
        manage_number,
        ARRAY_AGG(NULLIF(product_name, '') IGNORE NULLS ORDER BY LENGTH(product_name) DESC LIMIT 1)[OFFSET(0)] AS product_name
      FROM `{PROJECT_ID}.{BQ_DATASET}.product_master_raw`
      GROUP BY 1
    ),
    base_orders AS (
      SELECT
        order_number,
        user_email,
        order_datetime,
        DATE(order_datetime, "Asia/Tokyo") AS order_date,
        DATE_TRUNC(DATE(order_datetime, "Asia/Tokyo"), MONTH) AS order_month
      FROM `{PROJECT_ID}.{BQ_DATASET}.orders`
      WHERE order_status != '900'
    ),
    user_first_order AS (
      SELECT
        user_email,
        order_number AS first_order_number,
        order_date AS first_order_date,
        order_month AS first_order_month
      FROM (
        SELECT
          order_number,
          user_email,
          order_datetime,
          order_date,
          order_month,
          ROW_NUMBER() OVER(
            PARTITION BY user_email
            ORDER BY order_datetime ASC, order_number ASC
          ) AS rn
        FROM base_orders
      )
      WHERE rn = 1
    ),
    entry_products AS (
      SELECT
        u.user_email,
        u.first_order_number,
        u.first_order_date,
        u.first_order_month,
        i.manage_number AS entry_manage_number,
        COALESCE(pm.product_name, i.item_name) AS entry_item_name,
        i.subtotal,
        ROW_NUMBER() OVER(
          PARTITION BY u.user_email 
          ORDER BY i.subtotal DESC, i.manage_number ASC
        ) AS rn
      FROM user_first_order u
      JOIN `{PROJECT_ID}.{BQ_DATASET}.order_items` i
        ON i.order_number = u.first_order_number
      LEFT JOIN product_master pm
        ON pm.manage_number = i.manage_number
      WHERE i.manage_number IS NOT NULL
    )
    SELECT
      user_email,
      first_order_number,
      first_order_date,
      first_order_month,
      entry_manage_number,
      entry_item_name,
      CURRENT_TIMESTAMP() AS updated_at
    FROM entry_products
    WHERE rn = 1
    """
    
    logging.info("Initializing user_first_purchase_info (all periods)...")
    job = client.query(sql)
    result = job.result()
    
    logging.info(f"user_first_purchase_info initialized: {result.total_rows} users")
    return result.total_rows


def initialize_entry_product_ltv():
    """LTV集計テーブルに全期間のデータを投入"""
    from ltv_updater import update_entry_product_ltv
    from datetime import datetime
    from zoneinfo import ZoneInfo
    
    # ダミーの日時（全期間を計算するため、任意の値でよい）
    dummy_date = datetime(2020, 1, 1, tzinfo=ZoneInfo("Asia/Tokyo"))
    
    logging.info("Initializing entry_product_ltv_by_month_offset (all periods)...")
    update_entry_product_ltv(dummy_date)
    logging.info("entry_product_ltv_by_month_offset initialized")


def main():
    """初期化メイン処理"""
    logging.info("=== Starting LTV tables initialization ===")
    
    # 1) 初回購入情報テーブルの初期化
    try:
        user_count = initialize_user_first_purchase_info()
        logging.info(f"✅ user_first_purchase_info initialized: {user_count} users")
    except Exception as e:
        logging.error(f"❌ Failed to initialize user_first_purchase_info: {e}", exc_info=True)
        return
    
    # 2) LTVテーブルの初期化
    try:
        initialize_entry_product_ltv()
        logging.info("✅ entry_product_ltv_by_month_offset initialized")
    except Exception as e:
        logging.error(f"❌ Failed to initialize entry_product_ltv_by_month_offset: {e}", exc_info=True)
        return
    
    logging.info("=== LTV tables initialization completed successfully ===")


if __name__ == "__main__":
    main()
