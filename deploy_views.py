import os
import logging
from google.cloud import bigquery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)

# Configuration
PROJECT_ID = os.getenv("PROJECT_ID")
BQ_DATASET = os.getenv("BQ_DATASET", "rakuten_orders")
BQ_TABLE_ORDERS = os.getenv("BQ_TABLE_ORDERS", "orders")
BQ_TABLE_ORDER_ITEMS = os.getenv("BQ_TABLE_ORDER_ITEMS", "order_items")
BQ_TABLE_PRODUCT_MASTER_RAW = os.getenv("BQ_TABLE_PRODUCT_MASTER_RAW", "product_master_raw")
BQ_LOCATION = os.getenv("BQ_LOCATION", "asia-northeast1")

if not PROJECT_ID:
    raise ValueError("PROJECT_ID environment variable is not set")

def get_client():
    return bigquery.Client(project=PROJECT_ID, location=BQ_LOCATION)

def create_user_first_purchase_table():
    """初回購入情報テーブルを作成"""
    client = get_client()
    table_id = f"{PROJECT_ID}.{BQ_DATASET}.user_first_purchase_info"
    
    ddl = f"""
    CREATE TABLE IF NOT EXISTS `{table_id}` (
      user_email STRING NOT NULL,
      first_order_number STRING NOT NULL,
      first_order_date DATE NOT NULL,
      first_order_month DATE NOT NULL,
      entry_manage_number STRING NOT NULL,
      entry_item_name STRING,
      updated_at TIMESTAMP NOT NULL
    )
    OPTIONS(
      description="初回購入者情報テーブル"
    )
    """
    
    job = client.query(ddl)
    job.result()
    logging.info(f"Created/Updated table: {table_id}")


def create_ltv_table():
    """LTV集計テーブルを作成"""
    client = get_client()
    table_id = f"{PROJECT_ID}.{BQ_DATASET}.entry_product_ltv_by_month_offset"
    
    ddl = f"""
    CREATE TABLE IF NOT EXISTS `{table_id}` (
      entry_manage_number STRING NOT NULL,
      entry_item_name STRING,
      category_name STRING,
      brand_name STRING,
      first_order_month DATE NOT NULL,
      month_offset INT64 NOT NULL,
      cohort_users INT64 NOT NULL,
      active_buyers INT64 NOT NULL,
      revenue_in_month NUMERIC NOT NULL,
      cumulative_revenue NUMERIC NOT NULL,
      ltv_per_user NUMERIC,
      aov_in_month NUMERIC,
      updated_at TIMESTAMP NOT NULL
    )
    PARTITION BY first_order_month
    CLUSTER BY entry_manage_number, month_offset
    OPTIONS(
      description="入口商品別LTVテーブル"
    )
    """
    
    job = client.query(ddl)
    job.result()
    logging.info(f"Created/Updated table: {table_id}")

def create_view(view_name, sql):
    client = get_client()
    view_id = f"{PROJECT_ID}.{BQ_DATASET}.{view_name}"
    view = bigquery.Table(view_id)
    view.view_query = sql
    
    # Create or update the view
    # create_table with exists_ok=True does NOT update the view definition if it exists.
    # We must explicitly delete or update.
    client.delete_table(view_id, not_found_ok=True)
    view = client.create_table(view)
    logging.info(f"Created/Updated view: {view_id}")

def create_view_ddl(view_name, ddl):
    client = get_client()
    job = client.query(ddl)
    job.result()
    logging.info(f"Created/Updated view (DDL): {PROJECT_ID}.{BQ_DATASET}.{view_name}")

def main():
    # テーブル作成（初回のみ実行、既存の場合はスキップ）
    create_user_first_purchase_table()
    create_ltv_table()
    
    # 1. view_monthly_ltv
    sql_ltv = f"""
    WITH base_orders AS (
        SELECT
            order_number,
            user_email,
            total_price,
            order_datetime,
            DATE(order_datetime, "Asia/Tokyo") as order_date,
            DATE_TRUNC(DATE(order_datetime, "Asia/Tokyo"), MONTH) as order_month
        FROM `{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE_ORDERS}`
        WHERE order_status != '900' -- Exclude Cancelled
    ),
    user_orders_ranked AS (
        SELECT
            user_email,
            DATE(order_datetime, "Asia/Tokyo") as order_date,
            RANK() OVER(PARTITION BY user_email ORDER BY order_datetime ASC) as rn
        FROM base_orders
    ),
    user_milestones AS (
        SELECT
            user_email,
            MIN(CASE WHEN rn=1 THEN order_date END) as first_order_date,
            MIN(CASE WHEN rn=2 THEN order_date END) as second_order_date
        FROM user_orders_ranked
        GROUP BY 1
    ),
    months AS (
        SELECT DISTINCT order_month FROM base_orders
    ),
    monthly_metrics AS (
        SELECT
            o.order_month,
            COUNT(DISTINCT o.user_email) as monthly_unique_buyers,
            COUNT(o.order_number) as monthly_purchases,
            SUM(o.total_price) as monthly_sales,
            SAFE_DIVIDE(SUM(o.total_price), COUNT(o.order_number)) as aov,
            -- New Buyers (First order date is in this month)
            COUNT(DISTINCT CASE WHEN um.first_order_date >= o.order_month AND um.first_order_date < DATE_ADD(o.order_month, INTERVAL 1 MONTH) THEN o.user_email END) as new_buyers,
            -- Existing Active Buyers (First order was before this month)
            COUNT(DISTINCT CASE WHEN um.first_order_date < o.order_month THEN o.user_email END) as existing_active_buyers,
            -- Sales from Existing
            SUM(CASE WHEN um.first_order_date < o.order_month THEN o.total_price ELSE 0 END) as existing_sales
        FROM base_orders o
        JOIN user_milestones um ON o.user_email = um.user_email
        GROUP BY 1
    ),
    cumulative_metrics AS (
        SELECT
            m.order_month,
            -- Cumulative Users (First order <= End of this Month)
            (SELECT COUNT(*) FROM user_milestones u WHERE u.first_order_date < DATE_ADD(m.order_month, INTERVAL 1 MONTH)) as cum_total_users,
            -- Cumulative Repeaters (Second order <= End of this Month)
            (SELECT COUNT(*) FROM user_milestones u WHERE u.second_order_date < DATE_ADD(m.order_month, INTERVAL 1 MONTH)) as cum_repeat_users
        FROM months m
    )
    SELECT
        m.order_month as target_month,
        m.monthly_unique_buyers as unique_buyers,
        m.monthly_purchases,
        m.monthly_sales,
        m.aov,
        m.new_buyers as first_time_buyers,
        SAFE_DIVIDE(m.new_buyers, m.monthly_unique_buyers) as new_buyer_ratio,
        SAFE_DIVIDE(m.existing_active_buyers, m.monthly_unique_buyers) as repeat_rate_monthly,
        SAFE_DIVIDE(c.cum_repeat_users, c.cum_total_users) as repeat_rate_cumulative,
        SAFE_DIVIDE(m.existing_sales, NULLIF(m.existing_active_buyers, 0)) as existing_customer_aov
    FROM monthly_metrics m
    JOIN cumulative_metrics c ON m.order_month = c.order_month
    ORDER BY 1 DESC
    """
    create_view("view_monthly_ltv", sql_ltv)

    # 2. view_manageNumber_sales (蝠・刀邂｡逅・分蜿ｷ邊貞ｺｦ)
    sql_manage = f"""
    WITH product_master AS (
        SELECT
            manage_number,
            ARRAY_AGG(NULLIF(product_name, '') IGNORE NULLS ORDER BY LENGTH(product_name) DESC LIMIT 1)[OFFSET(0)] AS product_name
        FROM `{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE_PRODUCT_MASTER_RAW}`
        GROUP BY 1
    ),
    manage_monthly AS (
        SELECT
            DATE_TRUNC(DATE(o.order_datetime, "Asia/Tokyo"), MONTH) AS month,
            i.manage_number,
            ANY_VALUE(COALESCE(pm.product_name, i.item_name)) AS item_name,
            SUM(i.quantity) AS total_quantity,
            SUM(i.subtotal) AS total_sales,
            SAFE_DIVIDE(SUM(i.subtotal), NULLIF(SUM(i.quantity), 0)) AS avg_unit_price,
            COUNT(DISTINCT i.order_number) AS order_count,
            COUNT(DISTINCT o.user_email) AS unique_buyers
        FROM `{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE_ORDER_ITEMS}` i
        JOIN `{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE_ORDERS}` o ON i.order_number = o.order_number
        LEFT JOIN product_master pm ON pm.manage_number = i.manage_number
        WHERE o.order_status != '900'
        GROUP BY 1, 2
    )
    SELECT
        month,
        manage_number,
        item_name,
        total_quantity,
        total_sales,
        avg_unit_price,
        order_count,
        unique_buyers,
        SAFE_DIVIDE(total_sales, SUM(total_sales) OVER (PARTITION BY month)) AS sales_share_total
    FROM manage_monthly
    ORDER BY month DESC, total_sales DESC
    """
    create_view("view_manageNumber_sales", sql_manage)

    # 3. view_variantId_sales (SKU邂｡逅・分蜿ｷ邊貞ｺｦ)
    sql_variant = f"""
    WITH product_master AS (
        SELECT
            manage_number,
            ARRAY_AGG(NULLIF(product_name, '') IGNORE NULLS ORDER BY LENGTH(product_name) DESC LIMIT 1)[OFFSET(0)] AS product_name
        FROM `{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE_PRODUCT_MASTER_RAW}`
        GROUP BY 1
    ),
    sku_master AS (
        SELECT
            manage_number,
            variant_id,
            ARRAY_AGG(NULLIF(variation_name_value, '') IGNORE NULLS ORDER BY LENGTH(variation_name_value) DESC LIMIT 1)[OFFSET(0)] AS variation_name_value
        FROM `{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE_PRODUCT_MASTER_RAW}`
        GROUP BY 1, 2
    ),
    variant_monthly AS (
        SELECT
            DATE_TRUNC(DATE(o.order_datetime, "Asia/Tokyo"), MONTH) AS month,
            i.manage_number,
            i.variant_id,
            ANY_VALUE(COALESCE(sm.variation_name_value, i.sku_info)) AS variation_name_value,
            ANY_VALUE(i.sku_info) AS sku_info,
            ANY_VALUE(COALESCE(pm.product_name, i.item_name)) AS item_name,
            SUM(i.quantity) AS total_quantity,
            SUM(i.subtotal) AS total_sales,
            SAFE_DIVIDE(SUM(i.subtotal), NULLIF(SUM(i.quantity), 0)) AS avg_unit_price,
            COUNT(DISTINCT i.order_number) AS order_count,
            COUNT(DISTINCT o.user_email) AS unique_buyers
        FROM `{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE_ORDER_ITEMS}` i
        JOIN `{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE_ORDERS}` o ON i.order_number = o.order_number
        LEFT JOIN product_master pm ON pm.manage_number = i.manage_number
        LEFT JOIN sku_master sm ON sm.manage_number = i.manage_number AND sm.variant_id = i.variant_id
        WHERE o.order_status != '900'
        GROUP BY 1, 2, 3
    )
    SELECT
        month,
        manage_number,
        variant_id,
        variation_name_value,
        sku_info,
        item_name,
        total_quantity,
        total_sales,
        avg_unit_price,
        order_count,
        unique_buyers,
        SAFE_DIVIDE(total_sales, SUM(total_sales) OVER (PARTITION BY month, manage_number)) AS sales_share_within_product
    FROM variant_monthly
    ORDER BY month DESC, total_sales DESC
    """
    create_view("view_variantId_sales", sql_variant)

    # 4. view_entry_product_ltv (entry product cohort LTV - テーブル参照版)
    sql_entry_ltv = f"""
    CREATE OR REPLACE VIEW `{PROJECT_ID}.{BQ_DATASET}.view_entry_product_ltv` (
        entry_manage_number OPTIONS(description="入口商品管理番号（manage_number）"),
        entry_item_name OPTIONS(description="入口商品名（商品マスタ優先）"),
        first_order_month OPTIONS(description="ショップデビュー月（初回購入月、JST）"),
        month_offset OPTIONS(description="初回購入月からの経過月数（0=初月）"),
        cohort_users OPTIONS(description="入口商品×デビュー月の人数（ユニークユーザー）"),
        active_buyers OPTIONS(description="該当月に購入があった人数"),
        revenue_in_month OPTIONS(description="該当月の売上合計（orders.total_price）"),
        cumulative_revenue OPTIONS(description="初月からの累計売上"),
        ltv_per_user OPTIONS(description="1人あたりLTV（累計売上/コホート人数）"),
        aov_in_month OPTIONS(description="該当月の購入単価（売上/購入人数）")
    ) AS
    SELECT
        entry_manage_number,
        entry_item_name,
        first_order_month,
        month_offset,
        cohort_users,
        active_buyers,
        revenue_in_month,
        cumulative_revenue,
        ltv_per_user,
        aov_in_month
    FROM `{PROJECT_ID}.{BQ_DATASET}.entry_product_ltv_by_month_offset`
    ORDER BY first_order_month DESC, entry_manage_number, month_offset
    """
    create_view_ddl("view_entry_product_ltv", sql_entry_ltv)

if __name__ == "__main__":
    main()
