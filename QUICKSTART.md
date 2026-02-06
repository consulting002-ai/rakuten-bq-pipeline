# クイックスタート - デプロイ手順

このガイドでは、APIキー更新からCloud Functionsデプロイまでの手順を最短で実行します。

## 前提条件

- `gcloud` CLI がインストール済み
- PowerShell を使用（Windows）
- GCPプロジェクトへのアクセス権限あり

---

## ステップ1: 認証とプロジェクト設定

```powershell
# GCPにログイン
gcloud auth login

# プロジェクトを設定
gcloud config set project smarttanpaku-ltv-dev

# 確認
gcloud config get-value project
```

---

## ステップ2: APIキーの更新（必要な場合のみ）

### 方法A: スクリプトを使用（推奨）

```powershell
# Secret Managerの既存状態を確認
.\update_secrets.ps1 -ListOnly

# APIキーを更新（対話式で入力）
.\update_secrets.ps1
```

### 方法B: 手動で更新

```powershell
# SERVICE_SECRETを更新
echo -n "新しいSERVICE_SECRET値" | gcloud secrets versions add rakuten-service-secret --data-file=- --project=smarttanpaku-ltv-dev

# LICENSE_KEYを更新
echo -n "新しいLICENSE_KEY値" | gcloud secrets versions add rakuten-license-key --data-file=- --project=smarttanpaku-ltv-dev
```

---

## ステップ3: Cloud Functionsのデプロイ

### 方法A: スクリプトを使用（推奨）

```powershell
# デプロイコマンドを確認（実際には実行しない）
.\deploy.ps1 -DryRun

# 実際にデプロイ
.\deploy.ps1
```

### 方法B: 手動でデプロイ

```powershell
gcloud functions deploy rakuten-etl `
  --gen2 `
  --runtime=python311 `
  --region=asia-northeast1 `
  --source=. `
  --entry-point=main `
  --trigger-http `
  --allow-unauthenticated `
  --memory=2GiB `
  --timeout=540s `
  --set-env-vars="PROJECT_ID=smarttanpaku-ltv-dev,BUCKET_NAME=smarttanpaku-ltv-dev-raw-jsons,BQ_DATASET=rakuten_orders,BQ_LOCATION=asia-northeast1,SKIP_LTV_UPDATE=false" `
  --project=smarttanpaku-ltv-dev
```

デプロイには **3〜5分** かかります。

---

## ステップ4: デプロイの確認

### 4-1. Cloud Functionの状態確認

```powershell
gcloud functions describe rakuten-etl --region=asia-northeast1 --gen2 --project=smarttanpaku-ltv-dev
```

`status: ACTIVE` であれば成功です。

### 4-2. エンドポイントURLの確認

デプロイ完了時に表示されるURLをメモしてください：

```
url: https://asia-northeast1-smarttanpaku-ltv-dev.cloudfunctions.net/rakuten-etl
```

---

## ステップ5: テスト実行

### DRY RUN（データ書き込みなし）

```powershell
$FUNCTION_URL = "https://asia-northeast1-smarttanpaku-ltv-dev.cloudfunctions.net/rakuten-etl"
Invoke-WebRequest -Uri "$FUNCTION_URL?mode=MONTHLY&dry_run=1" -Method Get
```

**確認ポイント**:
- ステータスコード: `200`
- レスポンスに `"status": "success"` が含まれる
- `order_numbers` に件数が表示される

### 実際の月次実行

DRY RUNが成功したら、実際にデータを取り込みます：

```powershell
Invoke-WebRequest -Uri "$FUNCTION_URL?mode=MONTHLY" -Method Get
```

---

## ステップ6: ログとデータの確認

### ログ確認

```powershell
gcloud functions logs read rakuten-etl --region=asia-northeast1 --limit=50 --project=smarttanpaku-ltv-dev
```

**確認すべきメッセージ**:
- ✅ `searchOrder: XXX order_numbers`
- ✅ `[BQ] Monthly replace completed`
- ✅ `初回購入情報更新成功`
- ✅ `LTVテーブル更新成功`

### BigQueryで確認

BigQuery Consoleで以下を実行：

```sql
-- 最新の注文データ
SELECT MAX(inserted_at), COUNT(*) 
FROM `smarttanpaku-ltv-dev.rakuten_orders.orders`;

-- LTVテーブルの更新
SELECT MAX(updated_at), COUNT(*) 
FROM `smarttanpaku-ltv-dev.rakuten_orders.entry_product_ltv_by_month_offset`;
```

---

## オプション: 定期実行の設定

毎月1日の午前2時に自動実行する場合：

```powershell
$FUNCTION_URL = "https://asia-northeast1-smarttanpaku-ltv-dev.cloudfunctions.net/rakuten-etl"

gcloud scheduler jobs create http rakuten-monthly-etl `
  --location=asia-northeast1 `
  --schedule="0 2 1 * *" `
  --uri="$FUNCTION_URL?mode=MONTHLY" `
  --http-method=GET `
  --time-zone="Asia/Tokyo" `
  --project=smarttanpaku-ltv-dev
```

---

## トラブルシューティング

### エラー: `Permission denied`

```powershell
# サービスアカウントを確認
$SA = gcloud functions describe rakuten-etl --region=asia-northeast1 --gen2 --format="value(serviceConfig.serviceAccountEmail)" --project=smarttanpaku-ltv-dev

# Secret Managerへのアクセス権限を付与
gcloud secrets add-iam-policy-binding rakuten-service-secret --member="serviceAccount:$SA" --role="roles/secretmanager.secretAccessor" --project=smarttanpaku-ltv-dev
gcloud secrets add-iam-policy-binding rakuten-license-key --member="serviceAccount:$SA" --role="roles/secretmanager.secretAccessor" --project=smarttanpaku-ltv-dev
```

### エラー: `searchOrderが0件`

APIキーが正しいか確認：

```powershell
# 最新バージョンが有効か確認
gcloud secrets versions list rakuten-service-secret --project=smarttanpaku-ltv-dev
gcloud secrets versions list rakuten-license-key --project=smarttanpaku-ltv-dev
```

### その他のエラー

詳細は `DEPLOYMENT_GUIDE.md` を参照してください。

---

## 完了チェックリスト

- [ ] gcloud 認証完了
- [ ] APIキー更新完了（必要な場合）
- [ ] Cloud Functions デプロイ完了（`status: ACTIVE`）
- [ ] DRY RUN テスト成功
- [ ] 実際の月次実行成功
- [ ] BigQuery にデータが保存されている
- [ ] LTVテーブルが更新されている
- [ ] （オプション）Cloud Scheduler 設定完了

すべて ✅ なら完了です！
