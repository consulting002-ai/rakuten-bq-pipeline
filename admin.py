import logging
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import make_response
from google.cloud import secretmanager

from config import PROJECT_ID, SHOP_NAME, RAKUTEN_LICENSE_KEY_ID
from utils import setup_cloud_logging, get_secret

JST = ZoneInfo("Asia/Tokyo")

LICENSE_KEY_SECRET_ID = RAKUTEN_LICENSE_KEY_ID


def admin(request):
    """
    管理用 Cloud Function エントリーポイント。
    IAP（Identity-Aware Proxy）で保護され、アクセスには Google 認証が必要。

    エンドポイント:
      GET  /update-license-key  → 更新フォームを表示
      POST /update-license-key  → licenseKey を更新
    """
    setup_cloud_logging()
    path = (request.path or "/").rstrip("/") or "/"

    if path == "/update-license-key":
        if request.method == "GET":
            return _serve_form()
        if request.method == "POST":
            return _handle_update(request)

    return make_response("Not found", 404)


# =========================
# IAP ヘッダーから呼び出し元メールを取得
# =========================
def _get_caller_email(request) -> str:
    """
    IAP が付与する X-Goog-Authenticated-User-Email ヘッダーからメールアドレスを返す。
    値の形式: "accounts.google.com:user@example.com"
    """
    raw = request.headers.get("X-Goog-Authenticated-User-Email", "")
    if ":" in raw:
        return raw.split(":", 1)[1]
    return raw or "unknown"


# =========================
# GET: 更新フォームを表示
# =========================
def _serve_form():
    html = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>licenseKey 更新</title>
  <style>
    body { font-family: sans-serif; max-width: 480px; margin: 60px auto; padding: 0 20px; color: #333; }
    h1 { font-size: 1.2rem; border-bottom: 1px solid #ddd; padding-bottom: 8px; }
    label { display: block; margin-top: 16px; font-weight: bold; }
    input[type=text] { width: 100%; padding: 8px; font-size: 1rem; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; margin-top: 4px; }
    button { margin-top: 16px; padding: 10px 28px; font-size: 1rem; background: #1a73e8; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
    button:hover { background: #1558b0; }
    .note { color: #666; font-size: 0.85rem; margin-top: 6px; }
  </style>
</head>
<body>
  <h1>楽天RMS licenseKey 更新</h1>
  <form method="POST" action="/update-license-key">
    <label for="license_key">新しい licenseKey</label>
    <input type="text" id="license_key" name="license_key" required
           placeholder="SLxxxxxx_xxxxxxxxxxxxxxxx" autocomplete="off">
    <p class="note">
      楽天RMS Web Service の認証情報ページで発行した licenseKey を貼り付けてください。<br>
      更新者のGoogleアカウントとともに記録されます。
    </p>
    <button type="submit">更新する</button>
  </form>
</body>
</html>"""
    return make_response(html, 200, {"Content-Type": "text/html; charset=utf-8"})


# =========================
# POST: licenseKey を更新
# =========================
def _handle_update(request):
    caller_email = _get_caller_email(request)
    license_key = (request.form.get("license_key") or "").strip()

    if not license_key:
        return make_response("license_key が空です。", 400)

    # Secret Manager に新バージョンを追加
    client = secretmanager.SecretManagerServiceClient()
    secret_name = f"projects/{PROJECT_ID}/secrets/{LICENSE_KEY_SECRET_ID}"
    client.add_secret_version(
        request={"parent": secret_name, "payload": {"data": license_key.encode()}}
    )

    now_jst = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S JST")
    logging.info(f"licenseKey updated by {caller_email} at {now_jst}")

    _notify_chatwork(caller_email, now_jst)

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>更新完了</title>
  <style>
    body {{ font-family: sans-serif; max-width: 480px; margin: 60px auto; padding: 0 20px; color: #333; }}
    h1 {{ font-size: 1.2rem; color: #188038; }}
    ul {{ line-height: 1.8; }}
  </style>
</head>
<body>
  <h1>✅ licenseKey を更新しました</h1>
  <ul>
    <li>更新者: {caller_email}</li>
    <li>更新日時: {now_jst}</li>
    <li>ショップ: {SHOP_NAME}</li>
  </ul>
</body>
</html>"""
    return make_response(html, 200, {"Content-Type": "text/html; charset=utf-8"})


# =========================
# Chatwork 通知
# =========================
def _notify_chatwork(caller_email: str, timestamp: str):
    try:
        token = get_secret("chatwork-api-token")
        room_id = get_secret("chatwork-room-id")
    except Exception as e:
        logging.warning(f"Chatwork通知の設定を取得できませんでした（通知をスキップ）: {e}")
        return

    message = (
        f"[info][title]🔑 licenseKey 更新通知[/title]"
        f"ショップ: {SHOP_NAME}\n"
        f"更新者: {caller_email}\n"
        f"更新日時: {timestamp}[/info]"
    )

    try:
        resp = requests.post(
            f"https://api.chatwork.com/v2/rooms/{room_id}/messages",
            headers={"X-ChatWorkToken": token},
            data={"body": message},
            timeout=10,
        )
        resp.raise_for_status()
        logging.info("Chatwork通知を送信しました")
    except Exception as e:
        logging.warning(f"Chatwork通知の送信に失敗しました: {e}")
