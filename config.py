# ローカル開発用: .env ファイルを自動ロード（python-dotenv が入っていない場合はスキップ）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import os

# ─── GCP / Google Cloud ───────────────────────────────────────────────────────
PROJECT_ID  = os.getenv("PROJECT_ID")
BUCKET_NAME = os.getenv("BUCKET_NAME")
BQ_DATASET  = os.getenv("BQ_DATASET", "rakuten_orders")
BQ_LOCATION = os.getenv("BQ_LOCATION", "asia-northeast1")

# ─── BigQuery テーブル名 ──────────────────────────────────────────────────────
BQ_TABLE_ORDERS              = os.getenv("BQ_TABLE_ORDERS", "orders")
BQ_TABLE_ORDER_ITEMS         = os.getenv("BQ_TABLE_ORDER_ITEMS", "order_items")
BQ_TABLE_PRODUCT_MASTER      = os.getenv("BQ_TABLE_PRODUCT_MASTER_RAW", "product_master_raw")
BQ_TABLE_USER_FIRST_PURCHASE = "user_first_purchase_info"
BQ_TABLE_LTV                 = "entry_product_ltv_by_month_offset"

# ─── Rakuten API ──────────────────────────────────────────────────────────────
RAKUTEN_API_BASE_URL = os.getenv("BASE_URL", "https://api.rms.rakuten.co.jp/es/2.0/order/")
RAKUTEN_MAX_RETRIES          = 5
RAKUTEN_PAGE_SIZE            = 100   # getOrder の1リクエスト最大件数（API仕様上限）
RAKUTEN_SEARCH_ORDER_PAGE_SIZE = 1000  # searchOrder の1リクエスト最大件数（API仕様上限 1000）
                                       # 100件×150ページ=15,000件上限を回避するため最大値を使用

# ─── Secret Manager のシークレットID ─────────────────────────────────────────
RAKUTEN_SERVICE_SECRET_ID = os.getenv("RAKUTEN_SERVICE_SECRET_ID", "rakuten-service-secret")
RAKUTEN_LICENSE_KEY_ID    = os.getenv("RAKUTEN_LICENSE_KEY_ID", "rakuten-license-key")

# ─── 機能フラグ ───────────────────────────────────────────────────────────────
_TRUTHY = ("true", "1", "t", "yes", "y")
STRICT_RAW_PER_BATCH        = os.getenv("STRICT_RAW_PER_BATCH", "false").lower() in _TRUTHY
SKIP_LTV_UPDATE             = os.getenv("SKIP_LTV_UPDATE", "false").lower() in _TRUTHY
PRODUCT_MASTER_SYNC_REQUIRED = os.getenv("PRODUCT_MASTER_SYNC_REQUIRED", "false").lower() in _TRUTHY

# ─── ドメイン定数 ─────────────────────────────────────────────────────────────
CANCEL_STATUS = "900"  # 楽天: キャンセル注文の order_status 値

# ─── 表示名（admin 用）───────────────────────────────────────────────────────
SHOP_NAME = os.getenv("SHOP_NAME", PROJECT_ID)
