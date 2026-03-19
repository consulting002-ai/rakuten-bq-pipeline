import os
import time
import base64
import logging
import requests

from config import RAKUTEN_API_BASE_URL as BASE_URL, RAKUTEN_MAX_RETRIES as MAX_RETRIES, RAKUTEN_PAGE_SIZE as PAGE_SIZE
from utils import get_rakuten_credentials

# Secret Managerから認証情報を取得（環境変数にフォールバック）
try:
    SERVICE_SECRET, LICENSE_KEY = get_rakuten_credentials()
except Exception as e:
    # Secret Manager取得に失敗した場合は環境変数から取得（後方互換性）
    logging.warning(
        f"Secret Managerからの認証情報取得に失敗しました。環境変数から取得します: {e}"
    )
    SERVICE_SECRET = os.getenv("RAKUTEN_SERVICE_SECRET")
    LICENSE_KEY = os.getenv("RAKUTEN_LICENSE_KEY")

# ここで正規化（クレンジング）
SERVICE_SECRET = (SERVICE_SECRET or "").strip()
LICENSE_KEY = (LICENSE_KEY or "").strip()


# ------------------------------
# 認証ヘッダー生成
# ------------------------------
def build_auth_header():
    """ESA認証ヘッダーを生成"""
    auth_str = f"{SERVICE_SECRET.strip()}:{LICENSE_KEY.strip()}"
    encoded = base64.b64encode(auth_str.encode()).decode()
    return {
        "Authorization": f"ESA {encoded}",
        "Content-Type": "application/json; charset=utf-8",
    }


# ------------------------------
# APIコールの共通関数
# ------------------------------
def call_api(endpoint, payload):
    """Rakuten APIを呼び出す共通関数（リトライ付き）"""
    url = f"{BASE_URL}{endpoint}"
    headers = build_auth_header()

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code in [429, 500, 503]:
                wait = 2**attempt
                logging.warning(
                    f"Retry {attempt+1}/{MAX_RETRIES} after {wait}s (status={resp.status_code})"
                )
                time.sleep(wait)
            else:
                logging.error(f"API Error {resp.status_code}: {resp.text}")
                break
        except Exception as e:
            logging.error(f"Request failed: {e}")
            time.sleep(2**attempt)
    return None


# ------------------------------
# searchOrder
# ------------------------------
def search_order(start_datetime, end_datetime):
    """???????????????"""
    logging.info(f"Fetching order numbers: {start_datetime} - {end_datetime}")
    all_orders = []
    page = 1

    while True:
        payload = {
            "dateType": 1,
            "startDatetime": start_datetime,
            "endDatetime": end_datetime,
            "PaginationRequestModel": {
                "requestRecordsAmount": PAGE_SIZE,
                "requestPage": page,
            },
        }
        data = call_api("searchOrder/", payload)
        if not data:
            break

        order_list = data.get("orderNumberList", []) or []
        all_orders.extend(order_list)
        logging.info(f"Page {page}: {len(order_list)} orders fetched")

        pagination = data.get("PaginationResponseModel") or {}
        current_page = pagination.get("requestPage") or page
        total_pages = pagination.get("totalPages")

        if total_pages is not None:
            if current_page >= total_pages:
                break
            page = current_page + 1
            continue

        if len(order_list) < PAGE_SIZE:
            break
        page += 1

    logging.info(f"Total order numbers: {len(all_orders)}")
    return all_orders



# ------------------------------
# getOrder
# ------------------------------
def get_order(order_numbers):
    """
    注文番号リストから注文詳細を取得
    - 100件単位でバッチ化して呼び出し
    """
    all_results = []
    for i in range(0, len(order_numbers), PAGE_SIZE):
        batch = order_numbers[i : i + PAGE_SIZE]
        payload = {"orderNumberList": batch, "version": 9}
        logging.info(
            f"Fetching details for {len(batch)} orders (batch {i//PAGE_SIZE+1})"
        )

        data = call_api("getOrder/", payload)
        if not data:
            continue

        order_models = data.get("OrderModelList", [])
        all_results.extend(order_models)

    logging.info(f"Total orders fetched: {len(all_results)}")
    return all_results
