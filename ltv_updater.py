import logging
from datetime import datetime
from google.cloud import bigquery
from typing import Optional

from config import PROJECT_ID, BQ_DATASET, BQ_LOCATION


def get_client():
    return bigquery.Client(project=PROJECT_ID, location=BQ_LOCATION)


def update_user_first_purchase_info(processed_month_start: datetime) -> dict:
    """
    初回購入情報テーブルを更新（該当月の新規ユーザーのみ）
    
    Args:
        processed_month_start: 処理対象月の月初（JST）
    
    Returns:
        dict: 更新結果（inserted_users数など）
    """
    client = get_client()
    
    # 処理対象月の開始・終了を計算
    from dateutil.relativedelta import relativedelta
    month_start = processed_month_start.strftime("%Y-%m-%d")
    month_end = (processed_month_start + relativedelta(months=1)).strftime("%Y-%m-%d")
    
    sql = f"""
    MERGE `{PROJECT_ID}.{BQ_DATASET}.user_first_purchase_info` AS T
    USING (
      WITH product_master AS (
        SELECT
          manage_number,
          ARRAY_AGG(NULLIF(product_name, '') IGNORE NULLS ORDER BY LENGTH(product_name) DESC LIMIT 1)[OFFSET(0)] AS product_name,
          ARRAY_AGG(NULLIF(category_name, '') IGNORE NULLS ORDER BY LENGTH(category_name) DESC LIMIT 1)[OFFSET(0)] AS category_name,
          ARRAY_AGG(NULLIF(brand_name, '') IGNORE NULLS ORDER BY LENGTH(brand_name) DESC LIMIT 1)[OFFSET(0)] AS brand_name
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
          AND order_month >= '{month_start}'
          AND order_month < '{month_end}'
      ),
      entry_products AS (
        SELECT
          u.user_email,
          u.first_order_number,
          u.first_order_date,
          u.first_order_month,
          i.manage_number AS entry_manage_number,
          COALESCE(pm.product_name, i.item_name) AS entry_item_name,
          pm.category_name AS category_name,
          pm.brand_name AS brand_name,
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
    ) AS S
    ON T.user_email = S.user_email
    WHEN NOT MATCHED THEN
      INSERT (user_email, first_order_number, first_order_date, first_order_month, 
              entry_manage_number, entry_item_name, updated_at)
      VALUES (S.user_email, S.first_order_number, S.first_order_date, S.first_order_month,
              S.entry_manage_number, S.entry_item_name, S.updated_at)
    """
    
    logging.info(f"Updating user_first_purchase_info for month: {month_start}")
    job = client.query(sql)
    result = job.result()
    
    # 挿入行数を取得
    stats = job._properties.get('statistics', {}).get('query', {})
    dml_stats = stats.get('dmlStats', {})
    inserted_rows = dml_stats.get('insertedRowCount', 0)
    
    logging.info(f"user_first_purchase_info updated: {inserted_rows} new users")
    
    return {
        "inserted_users": int(inserted_rows) if inserted_rows else 0,
        "month": month_start
    }


def update_entry_product_ltv(processed_month_start: datetime) -> dict:
    """
    LTV集計テーブルを更新
    
    該当月の新規データにより、過去のコホートの累計売上も変わる可能性があるため、
    全期間のデータを再計算する。
    
    Args:
        processed_month_start: 処理対象月の月初（JST）
    
    Returns:
        dict: 更新結果（affected_rows数など）
    """
    client = get_client()
    
    # LTV集計SQLを実行
    sql = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{BQ_DATASET}.entry_product_ltv_by_month_offset`
    PARTITION BY first_order_month
    CLUSTER BY entry_manage_number, month_offset
    AS
    WITH product_master AS (
      SELECT
        manage_number,
        ARRAY_AGG(NULLIF(product_name, '') IGNORE NULLS ORDER BY LENGTH(product_name) DESC LIMIT 1)[OFFSET(0)] AS product_name,
        ARRAY_AGG(NULLIF(category_name, '') IGNORE NULLS ORDER BY LENGTH(category_name) DESC LIMIT 1)[OFFSET(0)] AS category_name,
        ARRAY_AGG(NULLIF(brand_name, '') IGNORE NULLS ORDER BY LENGTH(brand_name) DESC LIMIT 1)[OFFSET(0)] AS brand_name
      FROM `{PROJECT_ID}.{BQ_DATASET}.product_master_raw`
      GROUP BY 1
    ),
    base_orders AS (
      SELECT
        user_email,
        total_price,
        DATE_TRUNC(DATE(order_datetime, "Asia/Tokyo"), MONTH) AS order_month
      FROM `{PROJECT_ID}.{BQ_DATASET}.orders`
      WHERE order_status != '900'
    ),
    user_monthly_sales AS (
      SELECT
        user_email,
        order_month,
        SUM(total_price) AS monthly_sales
      FROM base_orders
      GROUP BY 1, 2
    ),
    user_cohort_sales AS (
      SELECT
        ufp.entry_manage_number,
        COALESCE(pm.product_name, ufp.entry_item_name) AS entry_item_name,
        pm.category_name,
        pm.brand_name,
        ufp.first_order_month,
        DATE_DIFF(ums.order_month, ufp.first_order_month, MONTH) AS month_offset,
        ums.user_email,
        ums.monthly_sales
      FROM `{PROJECT_ID}.{BQ_DATASET}.user_first_purchase_info` ufp
      LEFT JOIN product_master pm ON pm.manage_number = ufp.entry_manage_number
      JOIN user_monthly_sales ums
        ON ufp.user_email = ums.user_email
      WHERE DATE_DIFF(ums.order_month, ufp.first_order_month, MONTH) >= 0
    ),
    cohort_counts AS (
      SELECT
        ufp.entry_manage_number,
        COALESCE(pm.product_name, ufp.entry_item_name) AS entry_item_name,
        pm.category_name,
        pm.brand_name,
        ufp.first_order_month,
        COUNT(DISTINCT ufp.user_email) AS cohort_users
      FROM `{PROJECT_ID}.{BQ_DATASET}.user_first_purchase_info` ufp
      LEFT JOIN product_master pm ON pm.manage_number = ufp.entry_manage_number
      GROUP BY 1, 2, 3, 4, 5
    ),
    monthly_aggregated AS (
      SELECT
        ucs.entry_manage_number,
        ucs.entry_item_name,
        ucs.category_name,
        ucs.brand_name,
        ucs.first_order_month,
        ucs.month_offset,
        cc.cohort_users,
        COUNT(DISTINCT ucs.user_email) AS active_buyers,
        SUM(ucs.monthly_sales) AS revenue_in_month
      FROM user_cohort_sales ucs
      JOIN cohort_counts cc
        ON ucs.entry_manage_number = cc.entry_manage_number
        AND ucs.first_order_month = cc.first_order_month
      GROUP BY 1, 2, 3, 4, 5, 6, 7
    )
    SELECT
      entry_manage_number,
      entry_item_name,
      category_name,
      brand_name,
      first_order_month,
      month_offset,
      cohort_users,
      active_buyers,
      revenue_in_month,
      SUM(revenue_in_month) OVER (
        PARTITION BY entry_manage_number, first_order_month 
        ORDER BY month_offset
      ) AS cumulative_revenue,
      SAFE_DIVIDE(
        SUM(revenue_in_month) OVER (
          PARTITION BY entry_manage_number, first_order_month 
          ORDER BY month_offset
        ),
        cohort_users
      ) AS ltv_per_user,
      SAFE_DIVIDE(revenue_in_month, NULLIF(active_buyers, 0)) AS aov_in_month,
      CURRENT_TIMESTAMP() AS updated_at
    FROM monthly_aggregated
    WHERE active_buyers > 0 OR revenue_in_month > 0
    """
    
    logging.info("Updating entry_product_ltv_by_month_offset (full recalculation)")
    job = client.query(sql)
    job.result()
    logging.info("entry_product_ltv_by_month_offset updated")

    return {}


def update_ltv_item_names_from_master() -> dict:
    """
    entry_product_ltv_by_month_offset の entry_item_name, category_name, brand_name を
    product_master_raw から再取得して更新
    
    商品マスタの商品名・カテゴリ名・ブランド名を変更した後、LTVテーブルに即座に反映させたい場合に使用。
    user_first_purchase_info は次回の月次更新時に自動的に同期される。
    
    Returns:
        dict: 更新結果（updated_rows数など）
    """
    client = get_client()
    
    sql = f"""
    MERGE `{PROJECT_ID}.{BQ_DATASET}.entry_product_ltv_by_month_offset` AS T
    USING (
      WITH product_master AS (
        SELECT
          manage_number,
          ARRAY_AGG(NULLIF(product_name, '') IGNORE NULLS 
                    ORDER BY LENGTH(product_name) DESC LIMIT 1)[OFFSET(0)] AS product_name,
          ARRAY_AGG(NULLIF(category_name, '') IGNORE NULLS 
                    ORDER BY LENGTH(category_name) DESC LIMIT 1)[OFFSET(0)] AS category_name,
          ARRAY_AGG(NULLIF(brand_name, '') IGNORE NULLS 
                    ORDER BY LENGTH(brand_name) DESC LIMIT 1)[OFFSET(0)] AS brand_name
        FROM `{PROJECT_ID}.{BQ_DATASET}.product_master_raw`
        GROUP BY 1
      ),
      order_items_with_master AS (
        SELECT DISTINCT
          oi.manage_number,
          pm.product_name AS latest_item_name,
          pm.category_name AS latest_category_name,
          pm.brand_name AS latest_brand_name
        FROM `{PROJECT_ID}.{BQ_DATASET}.order_items` oi
        INNER JOIN product_master pm ON pm.manage_number = oi.manage_number
      )
      SELECT
        manage_number AS entry_manage_number,
        latest_item_name AS new_entry_item_name,
        latest_category_name AS new_category_name,
        latest_brand_name AS new_brand_name
      FROM order_items_with_master
    ) AS S
    ON T.entry_manage_number = S.entry_manage_number
    WHEN MATCHED AND (
      T.entry_item_name != S.new_entry_item_name OR
      IFNULL(T.category_name, '') != IFNULL(S.new_category_name, '') OR
      IFNULL(T.brand_name, '') != IFNULL(S.new_brand_name, '')
    ) THEN
      UPDATE SET 
        entry_item_name = S.new_entry_item_name,
        category_name = S.new_category_name,
        brand_name = S.new_brand_name,
        updated_at = CURRENT_TIMESTAMP()
    """
    
    logging.info("Updating entry_item_names in LTV table from product_master...")
    job = client.query(sql)
    result = job.result()
    
    # 更新行数を取得
    stats = job._properties.get('statistics', {}).get('query', {})
    dml_stats = stats.get('dmlStats', {})
    updated_rows = dml_stats.get('updatedRowCount', 0)
    
    logging.info(f"LTV entry_item_names updated: {updated_rows} rows")
    
    return {
        "updated_rows": int(updated_rows) if updated_rows else 0
    }
