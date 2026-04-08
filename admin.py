import logging
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import make_response
from google.cloud import secretmanager
from google.protobuf import field_mask_pb2

from config import PROJECT_ID, SHOP_NAME, RAKUTEN_LICENSE_KEY_ID
from utils import setup_cloud_logging, get_secret, get_secret_label

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
            try:
                expiry_label = get_secret_label(LICENSE_KEY_SECRET_ID, "expiry-date")
                current_expiry = expiry_label.replace("-", "/") if expiry_label else ""
            except Exception:
                current_expiry = ""
            return _serve_form(current_expiry=current_expiry)
        if request.method == "POST":
            return _handle_update(request)

    return make_response("Not found", 404)


# =========================
# GET: 更新フォームを表示
# =========================
def _serve_form(error: str = "", current_expiry: str = ""):
    error_html = f'<p class="error">{error}</p>' if error else ""
    expiry_value = f' value="{current_expiry}"' if current_expiry else ""
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{SHOP_NAME} ライセンスキー更新</title>
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
  <h1>LTVデータ作成用 ライセンスキー更新（{SHOP_NAME}）</h1>
  {error_html}
  <form method="POST" action="">
    <label for="current_license_key">現在のライセンスキー（確認用）</label>
    <input type="password" id="current_license_key" name="current_license_key" required
           placeholder="SLxxxxxx_xxxxxxxxxxxxxxxx" autocomplete="off">

    <label for="new_license_key">新しいライセンスキー</label>
    <input type="text" id="new_license_key" name="new_license_key" required
           placeholder="SLxxxxxx_xxxxxxxxxxxxxxxx" autocomplete="off">

    <label for="new_expiry_date">新しいライセンスキーの有効期限</label>
    <input type="text" id="new_expiry_date" name="new_expiry_date" required
           placeholder="2026/07/02" autocomplete="off"{expiry_value}>
    <p class="note">有効期限は楽天 RMS の「ライセンス管理」ページで確認できます。形式: YYYY/MM/DD</p>

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
    new_expiry_date = (request.form.get("new_expiry_date") or "").strip()

    if not current_license_key or not new_license_key or not new_expiry_date:
        return _serve_form(error="すべての項目を入力してください。", current_expiry=new_expiry_date)

    # 有効期限のフォーマット検証（YYYY/MM/DD）
    try:
        datetime.strptime(new_expiry_date, "%Y/%m/%d")
    except ValueError:
        return _serve_form(
            error="有効期限の形式が正しくありません。YYYY/MM/DD 形式で入力してください（例: 2026/07/02）。",
            current_expiry=new_expiry_date,
        )

    # 現在のライセンスキーを Secret Manager から取得して照合
    try:
        stored_license_key = get_secret(LICENSE_KEY_SECRET_ID)
    except Exception as e:
        logging.error(f"現在のライセンスキー取得失敗: {e}")
        return _serve_form(
            error="現在のライセンスキーの取得に失敗しました。しばらくして再試行してください。",
            current_expiry=new_expiry_date,
        )

    if current_license_key != stored_license_key:
        logging.warning("ライセンスキー更新失敗: 現在のライセンスキーが一致しません")
        return _serve_form(error="現在のライセンスキーが正しくありません。", current_expiry=new_expiry_date)

    client = secretmanager.SecretManagerServiceClient()
    secret_name = f"projects/{PROJECT_ID}/secrets/{LICENSE_KEY_SECRET_ID}"

    # 新しい licenseKey を Secret Manager に登録
    client.add_secret_version(
        request={"parent": secret_name, "payload": {"data": new_license_key.encode()}}
    )

    # 有効期限ラベルを更新（既存のラベルを保持しつつ expiry-date を上書き）
    expiry_label = new_expiry_date.replace("/", "-")  # "2026/07/02" → "2026-07-02"
    existing_secret = client.get_secret(request={"name": secret_name})
    merged_labels = dict(existing_secret.labels)
    merged_labels["expiry-date"] = expiry_label
    client.update_secret(
        request={
            "secret": {"name": secret_name, "labels": merged_labels},
            "update_mask": field_mask_pb2.FieldMask(paths=["labels"]),
        }
    )

    now_jst = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S JST")
    logging.info(f"licenseKey updated at {now_jst}, expiry: {new_expiry_date}")

    notify_chatwork(
        title=f"🔑 licenseKey 更新通知（{SHOP_NAME}）",
        body=(
            f"ショップ: {SHOP_NAME}\n"
            f"更新日時: {now_jst}\n"
            f"新しい有効期限: {new_expiry_date}"
        ),
    )

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
    <li>新しい有効期限: {new_expiry_date}</li>
  </ul>
</body>
</html>"""
    return make_response(html, 200, {"Content-Type": "text/html; charset=utf-8"})


# =========================
# Chatwork 通知
# =========================
def notify_chatwork(title: str, body: str) -> None:
    """Chatwork にメッセージを送信する（送信失敗は警告ログに留め、呼び出し元の処理を止めない）"""
    try:
        token = get_secret("chatwork-api-token")
        room_id = get_secret("chatwork-room-id")
    except Exception as e:
        logging.warning(f"Chatwork通知の設定を取得できませんでした（通知をスキップ）: {e}")
        return

    message = f"[info][title]{title}[/title]{body}[/info]"

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
