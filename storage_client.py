import json
import logging
from datetime import datetime
from google.cloud import storage

from config import BUCKET_NAME, PROJECT_ID

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
