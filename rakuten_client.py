import os
import time
import base64
import logging
import requests

from config import (
    RAKUTEN_API_BASE_URL as BASE_URL,
    RAKUTEN_MAX_RETRIES as MAX_RETRIES,
    RAKUTEN_PAGE_SIZE as PAGE_SIZE,
    RAKUTEN_SEARCH_ORDER_PAGE_SIZE as SEARCH_PAGE_SIZE,
)
from utils import get_rakuten_credentials


# ------------------------------
# 認証ヘッダー生成
# ------------------------------
def build_auth_header():
    """ESA認証ヘッダーを生成（毎回 Secret Manager から最新の認証情報を取得）"""
    try:
        service_secret, license_key = get_rakuten_credentials()
    except Exception as e:
        logging.warning(f"Secret Managerからの認証情報取得に失敗しました。環境変数から取得します: {e}")
        service_secret = os.getenv("RAKUTEN_SERVICE_SECRET", "")
        license_key = os.getenv("RAKUTEN_LICENSE_KEY", "")

    service_secret = (service_secret or "").strip()
    license_key = (license_key or "").strip()

    auth_str = f"{service_secret}:{license_key}"
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
            elif resp.status_code == 401:
                # GA0001: Un-Authorised（ライセンスキー期限切れ・認証情報不正）
                raise RuntimeError(
                    f"Rakuten API 認証失敗 (HTTP 401 GA0001): ライセンスキーを確認してください。"
                    f" レスポンス: {resp.text}"
                )
            elif resp.status_code == 400:
                # GK0001/GK0005/GK0006: 認証情報の構造的問題、またはリクエストパラメータ不正
                raise RuntimeError(
                    f"Rakuten API リクエストエラー (HTTP 400): 認証情報またはリクエスト内容を確認してください。"
                    f" レスポンス: {resp.text}"
                )
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
    """指定期間の注文番号一覧を取得する（ページネーション対応）。
    
    1ページあたり最大 SEARCH_PAGE_SIZE=1000 件を使用する。
    PAGE_SIZE=100 を使うと 100件×最大150ページ=15,000件上限に達するため、
    ページサイズを最大値にしてこの制約を回避している。
    """
    logging.info(f"Fetching order numbers: {start_datetime} - {end_datetime}")
    all_orders = []
    page = 1

    while True:
        payload = {
            "dateType": 1,
            "startDatetime": start_datetime,
            "endDatetime": end_datetime,
            "PaginationRequestModel": {
                "requestRecordsAmount": SEARCH_PAGE_SIZE,
                "requestPage": page,
            },
        }
        data = call_api("searchOrder/", payload)
        if not data:
            break

        order_list = data.get("orderNumberList", []) or []
        all_orders.extend(order_list)
        logging.info(f"Page {page}: {len(order_list)} orders fetched (累計: {len(all_orders)})")

        pagination = data.get("PaginationResponseModel") or {}
        current_page = pagination.get("requestPage") or page
        total_pages = pagination.get("totalPages")

        if total_pages is not None:
            if current_page >= total_pages:
                break
            page = current_page + 1
            continue

        if len(order_list) < SEARCH_PAGE_SIZE:
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
