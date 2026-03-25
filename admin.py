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
    認証なしで公開。現在の licenseKey を入力することで本人確認を行う。

    エンドポイント:
      GET  /update-license-key  → 更新フォームを表示
      POST /update-license-key  → licenseKey を更新
    """
    setup_cloud_logging()
    path = (request.path or "/").rstrip("/") or "/"
    if path == "/update-license-key" or path.endswith("/update-license-key"):
        if request.method == "GET":
            return _serve_form()
        if request.method == "POST":
            return _handle_update(request)

    return make_response("Not found", 404)


# =========================
# GET: 更新フォームを表示
# =========================
def _serve_form(error: str = ""):
    error_html = f'<p class="error">{error}</p>' if error else ""
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>licenseKey 更新</title>
  <style>
    body {{ font-family: sans-serif; max-width: 480px; margin: 60px auto; padding: 0 20px; color: #333; }}
    h1 {{ font-size: 1.2rem; border-bottom: 1px solid #ddd; padding-bottom: 8px; }}
    label {{ display: block; margin-top: 16px; font-weight: bold; }}
    input[type=text], input[type=password] {{ width: 100%; padding: 8px; font-size: 1rem; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; margin-top: 4px; }}
    button {{ margin-top: 16px; padding: 10px 28px; font-size: 1rem; background: #1a73e8; color: #fff; border: none; border-radius: 4px; cursor: pointer; }}
    button:hover {{ background: #1558b0; }}
    .note {{ color: #666; font-size: 0.85rem; margin-top: 6px; }}
    .error {{ color: #c62828; font-weight: bold; margin-top: 12px; }}
  </style>
</head>
<body>
  <h1>楽天RMS licenseKey 更新（{SHOP_NAME}）</h1>
  {error_html}
  <form method="POST" action="">
    <label for="current_license_key">現在のライセンスキー（確認用）</label>
    <input type="password" id="current_license_key" name="current_license_key" required
           placeholder="現在登録されているライセンスキー" autocomplete="off">
    <p class="note">楽天RMSに現在登録されているライセンスキーを入力してください。</p>

    <label for="new_license_key">新しいライセンスキー</label>
    <input type="text" id="new_license_key" name="new_license_key" required
           placeholder="SLxxxxxx_xxxxxxxxxxxxxxxx" autocomplete="off">
    <p class="note">楽天RMS Web Service の認証情報ページで新たに発行したライセンスキーを貼り付けてください。</p>

    <button type="submit">更新する</button>
  </form>
</body>
</html>"""
    return make_response(html, 200, {"Content-Type": "text/html; charset=utf-8"})


# =========================
# POST: licenseKey を更新
# =========================
def _handle_update(request):
    current_license_key = (request.form.get("current_license_key") or "").strip()
    new_license_key = (request.form.get("new_license_key") or "").strip()

    if not current_license_key or not new_license_key:
        return _serve_form(error="すべての項目を入力してください。")

    # 現在のライセンスキーを Secret Manager から取得して照合
    try:
        stored_license_key = get_secret(LICENSE_KEY_SECRET_ID)
    except Exception as e:
        logging.error(f"現在のライセンスキー取得失敗: {e}")
        return _serve_form(error="現在のライセンスキーの取得に失敗しました。しばらくして再試行してください。")

    if current_license_key != stored_license_key:
        logging.warning("ライセンスキー更新失敗: 現在のライセンスキーが一致しません")
        return _serve_form(error="現在のライセンスキーが正しくありません。")

    # 新しい licenseKey を Secret Manager に登録
    client = secretmanager.SecretManagerServiceClient()
    secret_name = f"projects/{PROJECT_ID}/secrets/{LICENSE_KEY_SECRET_ID}"
    client.add_secret_version(
        request={"parent": secret_name, "payload": {"data": new_license_key.encode()}}
    )

    now_jst = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S JST")
    logging.info(f"licenseKey updated at {now_jst}")

    _notify_chatwork(now_jst)

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
  <h1>✅ ライセンスキーを更新しました</h1>
  <ul>
    <li>更新日時: {now_jst}</li>
    <li>ショップ: {SHOP_NAME}</li>
  </ul>
</body>
</html>"""
    return make_response(html, 200, {"Content-Type": "text/html; charset=utf-8"})


# =========================
# Chatwork 通知
# =========================
def _notify_chatwork(timestamp: str):
    try:
        token = get_secret("chatwork-api-token")
        room_id = get_secret("chatwork-room-id")
    except Exception as e:
        logging.warning(f"Chatwork通知の設定を取得できませんでした（通知をスキップ）: {e}")
        return

    message = (
        f"[info][title]🔑 licenseKey 更新通知[/title]"
        f"ショップ: {SHOP_NAME}\n"
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
