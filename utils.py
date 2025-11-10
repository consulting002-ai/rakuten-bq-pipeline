import os
import logging
from typing import Optional
from google.cloud import secretmanager
from google.cloud import logging as cloud_logging


# =========================
# Secret Manager からの認証情報取得
# =========================
def get_secret(secret_id: str, project_id: Optional[str] = None, version: str = "latest") -> str:
    """
    Secret Managerからシークレットを取得する
    
    Args:
        secret_id: シークレットID（例: "rakuten-service-secret"）
        project_id: GCPプロジェクトID（未指定の場合は環境変数PROJECT_IDから取得）
        version: シークレットのバージョン（デフォルト: "latest"）
    
    Returns:
        str: シークレットの値
    
    Raises:
        ValueError: シークレットが見つからない場合
        Exception: Secret Manager API呼び出しエラー
    """
    if not project_id:
        project_id = os.getenv("PROJECT_ID")
        if not project_id:
            raise ValueError("PROJECT_IDが環境変数に設定されていません。")
    
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
        response = client.access_secret_version(request={"name": name})
        secret_value = response.payload.data.decode("UTF-8")
        return secret_value
    except Exception as e:
        logging.error(f"Secret Managerから {secret_id} の取得に失敗しました: {e}")
        raise


def get_rakuten_credentials(project_id: Optional[str] = None) -> tuple[str, str]:
    """
    Rakuten APIの認証情報をSecret Managerから取得する
    
    Args:
        project_id: GCPプロジェクトID（未指定の場合は環境変数PROJECT_IDから取得）
    
    Returns:
        tuple[str, str]: (SERVICE_SECRET, LICENSE_KEY) のタプル
    
    Note:
        環境変数でシークレットIDを指定可能:
        - RAKUTEN_SERVICE_SECRET_ID (デフォルト: "rakuten-service-secret")
        - RAKUTEN_LICENSE_KEY_ID (デフォルト: "rakuten-license-key")
    """
    service_secret_id = os.getenv("RAKUTEN_SERVICE_SECRET_ID", "rakuten-service-secret")
    license_key_id = os.getenv("RAKUTEN_LICENSE_KEY_ID", "rakuten-license-key")
    
    service_secret = get_secret(service_secret_id, project_id)
    license_key = get_secret(license_key_id, project_id)
    
    return service_secret, license_key


# =========================
# Cloud Logging の設定
# =========================
def setup_cloud_logging(project_id: Optional[str] = None, log_name: str = "rakuten-bq-pipeline"):
    """
    Cloud Loggingを設定する
    
    Args:
        project_id: GCPプロジェクトID（未指定の場合は環境変数PROJECT_IDから取得）
        log_name: ログ名（デフォルト: "rakuten-bq-pipeline"）
    
    Note:
        Cloud Functions環境では自動的にCloud Loggingに送信されるため、
        ローカル開発環境でのみ有効です。
    """
    if not project_id:
        project_id = os.getenv("PROJECT_ID")
    
    # Cloud Functions環境では標準出力が自動的にCloud Loggingに送信される
    # ローカル環境でのみCloud Loggingクライアントを使用
    if os.getenv("FUNCTION_TARGET") or os.getenv("K_SERVICE"):
        # Cloud Functions環境: 標準のlogging設定のみ
        logging.getLogger().setLevel(logging.INFO)
        logging.info("Cloud Functions環境で実行中。標準出力がCloud Loggingに送信されます。")
    else:
        # ローカル環境: Cloud Loggingクライアントを設定
        try:
            if project_id:
                client = cloud_logging.Client(project=project_id)
                client.setup_logging(log_level=logging.INFO)
                logging.info(f"Cloud Loggingが設定されました (project: {project_id}, log: {log_name})")
            else:
                logging.warning("PROJECT_IDが設定されていないため、標準ログ出力を使用します。")
                logging.getLogger().setLevel(logging.INFO)
        except Exception as e:
            logging.warning(f"Cloud Loggingの設定に失敗しました。標準ログ出力を使用します: {e}")
            logging.getLogger().setLevel(logging.INFO)

