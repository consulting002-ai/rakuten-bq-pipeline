# デプロイガイド - 運用時の手順

このガイドは**既存ショップの日常運用**向けです。新ショップの追加は `NEWSHOP.md` を参照してください。

> **CLIはすべて Cloud Shell から実行します。**
> GCP Console 右上の `>_` アイコンから起動してください。

## 目次
1. [デプロイの仕組み](#1-デプロイの仕組み)
2. [licenseKey の更新](#2-licensekey-の更新)
3. [デプロイ後の確認](#3-デプロイ後の確認)
4. [商品マスタの更新](#4-商品マスタの更新)
5. [トラブルシューティング](#5-トラブルシューティング)
6. [チェックリスト](#6-チェックリスト)
7. [ロールバック手順](#7-ロールバック手順)

---

## 1. デプロイの仕組み

### 自動デプロイ（通常）

`main` ブランチに push すると Cloud Build Trigger が起動し、自動でデプロイされます。

```
git push origin main
    ↓
Cloud Build Trigger（各GCPプロジェクトで設定済み）
    ↓
cloudbuild.yaml に従ってデプロイ
    ↓
Cloud Function 更新完了（環境変数はそのまま保持）
```

デプロイ状況は GCP Console → Cloud Build → 履歴 で確認できます。

### 環境変数の変更が必要な場合

SHEET_IDの変更など、環境変数を更新する必要がある場合のみ Cloud Shell から手動実行します：

```bash
gcloud functions deploy rakuten-etl \
  --gen2 \
  --region=asia-northeast1 \
  --update-env-vars="PRODUCT_MASTER_SHEET_ID=新しいID" \
  --project=YOUR_PROJECT_ID
```

---

## 2. licenseKey の更新

楽天RMS licenseKey は90日ごとに更新が必要です。

### ブラウザから更新（推奨）

```
https://asia-northeast1-YOUR_PROJECT_ID.cloudfunctions.net/rakuten-admin/update-license-key
```

上記URLにアクセス → Googleログイン → 新しい licenseKey を貼り付けて送信。
完了後 Chatwork に更新者・日時が通知されます。

### Cloud Shell から直接更新

```bash
read -s -p "新しい LICENSE_KEY を入力: " LIC_KEY && echo
echo -n "$LIC_KEY" | gcloud secrets versions add rakuten-license-key \
  --data-file=- \
  --project=YOUR_PROJECT_ID
```

### 現在のバージョン確認

```bash
gcloud secrets versions list rakuten-license-key --project=YOUR_PROJECT_ID
```

### 古いバージョンを無効化（オプション）

```bash
gcloud secrets versions disable 1 --secret=rakuten-license-key --project=YOUR_PROJECT_ID
```

---

## 3. デプロイ後の確認

### 3-1. Cloud Functionの状態確認

```bash
gcloud functions describe rakuten-etl \
  --region=asia-northeast1 \
  --gen2 \
  --project=YOUR_PROJECT_ID
```

### 3-2. DRY RUN テスト

```bash
FUNCTION_URL="https://asia-northeast1-YOUR_PROJECT_ID.cloudfunctions.net/rakuten-etl"
curl "$FUNCTION_URL?mode=MONTHLY&dry_run=1"
```

**確認ポイント**：
- レスポンスに `"status": "success"` が含まれること
- `order_numbers` に件数が表示されること

### 3-3. 実際の月次実行テスト

```bash
curl "$FUNCTION_URL?mode=MONTHLY"
```

### 3-4. ログの確認

```bash
gcloud functions logs read rakuten-etl \
  --region=asia-northeast1 \
  --limit=100 \
  --project=YOUR_PROJECT_ID
```

**確認すべきログ**:
- ✅ `searchOrder: XXX order_numbers`
- ✅ `[BQ] Monthly replace completed`
- ✅ `初回購入情報更新成功`
- ✅ `LTVテーブル更新成功`

### 3-5. BigQueryでデータ確認

```sql
SELECT MAX(inserted_at) AS last_inserted, COUNT(*) AS total_orders
FROM `YOUR_PROJECT_ID.rakuten_orders.orders`;

SELECT MAX(updated_at) AS last_updated, COUNT(*) AS total_rows
FROM `YOUR_PROJECT_ID.rakuten_orders.entry_product_ltv_by_month_offset`;
```

---

## 4. 商品マスタの更新

Googleスプレッドシートで商品名を変更した後、LTVテーブルに反映させます。

### 4-1. 更新の流れ

```
1. Googleスプレッドシートで商品名を修正
2. /sync-product-master エンドポイントを呼び出す
   → product_master_raw を最新に更新
   → entry_product_ltv_by_month_offset の商品名を更新
```

### 4-2. エンドポイントの呼び出し

```bash
FUNCTION_URL="https://asia-northeast1-YOUR_PROJECT_ID.cloudfunctions.net/rakuten-etl"
curl -X POST "$FUNCTION_URL/sync-product-master"
```

### 4-3. 注意事項

- ✅ **即座に反映**：`entry_product_ltv_by_month_offset` の商品名は即座に更新
- ⚠️ **次回月次更新で同期**：`user_first_purchase_info` は次回の月次更新時に自動同期
- ⚠️ **月次更新（午前2時）と同時実行は避けること**

---

## 5. トラブルシューティング

### `Permission denied`

**原因**：サービスアカウントに権限がない

```bash
# Cloud Functionのサービスアカウントを確認
gcloud functions describe rakuten-etl \
  --region=asia-northeast1 --gen2 \
  --format="value(serviceConfig.serviceAccountEmail)"

# Secret Managerへのアクセス権限を付与
gcloud secrets add-iam-policy-binding rakuten-service-secret \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/secretmanager.secretAccessor" \
  --project=YOUR_PROJECT_ID
```

### `Timeout`

**原因**：処理時間が540秒を超えている

**対策**：HISTORICALモードではなくMONTHLYモードを使用。または `DEPLOY_HISTORICAL.md` 参照。

### `searchOrder 0件`

**原因**：楽天RMS APIの認証エラー

**対策**：
1. Secret Managerの値が正しいか確認
2. 楽天RMS APIのステータスを確認
3. APIレート制限に達していないか確認

---

## 6. チェックリスト

- [ ] licenseKey が有効期限内である（90日ごとに更新）
- [ ] Cloud Function がデプロイされている（`status: ACTIVE`）
- [ ] DRY RUNでテストが成功する
- [ ] 月次実行が成功する
- [ ] BigQuery にデータが保存されている
- [ ] LTVテーブルが更新されている
- [ ] Cloud Storage に Raw JSON が保存されている
- [ ] Cloud Scheduler が設定されている

---

## 7. ロールバック手順

### licenseKey のロールバック

```bash
# 古いバージョンを有効化
gcloud secrets versions enable 1 --secret=rakuten-license-key --project=YOUR_PROJECT_ID

# 新しいバージョンを無効化
gcloud secrets versions disable 2 --secret=rakuten-license-key --project=YOUR_PROJECT_ID
```

### Cloud Functionのロールバック

GCP Console → Cloud Functions → `rakuten-etl` → リビジョン から以前のバージョンにトラフィックを切り替える。

---

## 参考リンク

- [Cloud Functions ドキュメント](https://cloud.google.com/functions/docs)
- [Cloud Build ドキュメント](https://cloud.google.com/build/docs)
- [Secret Manager ドキュメント](https://cloud.google.com/secret-manager/docs)
- [Cloud Scheduler ドキュメント](https://cloud.google.com/scheduler/docs)
