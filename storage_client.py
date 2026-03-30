import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from google.api_core.exceptions import PreconditionFailed
from google.cloud import storage

from config import BUCKET_NAME, PROJECT_ID

JST = ZoneInfo("Asia/Tokyo")

# -----------------------------------------
# GCSクライアント初期化
# -----------------------------------------
storage_client = storage.Client(project=PROJECT_ID)

# -----------------------------------------
# Raw JSONアップロード関数
# -----------------------------------------
def upload_raw_json(data, prefix="raw", batch_id=None):
    """
    Rakuten APIのRawレスポンスをGCSに保存する

    Args:
        data (dict or list): APIレスポンス(JSON形式)
        prefix (str): 保存先のプレフィックス（例: "raw"）
        batch_id (str): 任意の識別子（例: バッチ番号やページ番号）
    Returns:
        str: アップロード先のGCSパス
    """
    if not BUCKET_NAME:
        raise ValueError("環境変数 BUCKET_NAME が設定されていません。")

    # 保存パスを構築
    now = datetime.utcnow()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    batch_suffix = f"_{batch_id}" if batch_id else ""

    file_name = f"getOrder{batch_suffix}_{now.strftime('%Y%m%d_%H%M%S')}.json"
    blob_path = f"{prefix}/{year}/{month}/{file_name}"

    # JSON文字列化（日本語も可読で保存）
    json_str = json.dumps(data, ensure_ascii=False, indent=2)

    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(blob_path)
        blob.upload_from_string(json_str, content_type="application/json")

        gcs_uri = f"gs://{BUCKET_NAME}/{blob_path}"
        logging.info(f"✅ Raw JSON uploaded: {gcs_uri}")
        return gcs_uri

    except Exception as e:
        logging.error(f"❌ Failed to upload JSON to GCS: {e}")
        raise e

# -----------------------------------------
# 月次ロック（GCSベースの冪等実行制御）
# -----------------------------------------
def _lock_blob(year_month: str):
    """locks/monthly-YYYY-MM.lock の Blob オブジェクトを返す"""
    bucket = storage_client.bucket(BUCKET_NAME)
    return bucket.blob(f"locks/monthly-{year_month}.lock")


def acquire_monthly_lock(year_month: str) -> bool:
    """
    指定月のロックを取得する。
    GCS の if_generation_match=0 を利用した原子的書き込みで
    「ファイルが存在しない場合のみ作成」を保証する。

    Returns:
        True  … ロック取得成功（処理を続行してよい）
        False … 既にロックが存在する（実行中 or 完了済み → スキップ）
    """
    blob = _lock_blob(year_month)
    payload = json.dumps({
        "status": "running",
        "started_at": datetime.now(JST).isoformat(),
    })
    try:
        blob.upload_from_string(payload, content_type="application/json", if_generation_match=0)
        logging.info(f"🔒 月次ロック取得: {year_month}")
        return True
    except PreconditionFailed:
        existing = json.loads(blob.download_as_text())
        logging.warning(
            f"⏭️  月次ロック既存のためスキップ: {year_month} | {existing}"
        )
        return False


def complete_monthly_lock(year_month: str):
    """ロックファイルに完了ステータスを上書き記録する（処理成功時に呼ぶ）"""
    blob = _lock_blob(year_month)
    payload = json.dumps({
        "status": "completed",
        "completed_at": datetime.now(JST).isoformat(),
    })
    blob.upload_from_string(payload, content_type="application/json")
    logging.info(f"✅ 月次ロック完了マーク: {year_month}")


def release_monthly_lock(year_month: str):
    """
    ロックファイルを削除する（エラー時に手動リトライを可能にするために呼ぶ）。
    ファイルが存在しない場合はエラーを無視する。
    """
    try:
        _lock_blob(year_month).delete()
        logging.info(f"🔓 月次ロック解放: {year_month}")
    except Exception:
        pass


# -----------------------------------------
# テキストファイルやCSV保存も可能（将来拡張）
# -----------------------------------------
def upload_text(content, prefix="logs", filename="output.txt"):
    """
    任意のテキストファイルをGCSに保存
    """
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blob_path = f"{prefix}/{filename}"
        blob = bucket.blob(blob_path)
        blob.upload_from_string(content, content_type="text/plain")
        logging.info(f"📄 Text file uploaded: gs://{BUCKET_NAME}/{blob_path}")
        return f"gs://{BUCKET_NAME}/{blob_path}"
    except Exception as e:
        logging.error(f"Failed to upload text file: {e}")
        raise e
