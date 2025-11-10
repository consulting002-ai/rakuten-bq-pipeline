# Rakuten BigQuery Pipeline

楽天RMS APIから注文データを取得し、Cloud StorageにRaw JSONとして保存、BigQueryに正規化して取り込むETLパイプラインです。

## 概要

このプロジェクトは、楽天RMS APIから注文データを取得し、以下の処理を行います：

1. **データ取得**: 楽天RMS API（searchOrder/getOrder）から注文データを取得
2. **Raw保存**: 取得したデータをCloud StorageにJSON形式で保存
3. **データ正規化**: 注文データを`orders`と`order_items`の2つのテーブルに正規化
4. **BigQuery投入**: 正規化したデータをBigQueryに投入

## アーキテクチャ

```
Rakuten RMS API
    ↓
Cloud Functions (HTTP Trigger)
    ↓
┌─────────────────┬──────────────────┐
│  Cloud Storage  │   BigQuery       │
│  (Raw JSON)     │   (orders/       │
│                 │    order_items)  │
└─────────────────┴──────────────────┘
```

### 使用するGCPサービス

- **Cloud Functions**: ETL処理の実行
- **Cloud Storage**: Raw JSONデータの保存
- **BigQuery**: 正規化されたデータの保存
- **Cloud Tasks**: 過去データの一括取り込み（オプション）
- **Cloud Scheduler**: 定期実行（オプション）
- **Secret Manager**: 認証情報の管理
- **Cloud Logging**: ログ管理

## セットアップ

### 1. 前提条件

- Python 3.9以上
- Google Cloud Project
- 楽天RMS APIの認証情報（SERVICE_SECRET、LICENSE_KEY）

### 2. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 3. GCPサービスの有効化

```bash
gcloud services enable \
  cloudfunctions.googleapis.com \
  storage.googleapis.com \
  bigquery.googleapis.com \
  secretmanager.googleapis.com \
  cloudtasks.googleapis.com \
  --project=$PROJECT_ID
```

### 4. Secret Managerの設定

楽天RMS APIの認証情報をSecret Managerに保存：

```bash
# SERVICE_SECRETを保存
echo -n "your-service-secret" | gcloud secrets create rakuten-service-secret \
  --data-file=- \
  --project=$PROJECT_ID

# LICENSE_KEYを保存
echo -n "your-license-key" | gcloud secrets create rakuten-license-key \
  --data-file=- \
  --project=$PROJECT_ID
```

### 5. BigQueryデータセットとテーブルの作成

```sql
-- データセットの作成
CREATE SCHEMA IF NOT EXISTS `your-project.rakuten_orders`
  OPTIONS(
    location="asia-northeast1"
  );

-- ordersテーブルの作成（スキーマはtransform.pyを参照）
-- order_itemsテーブルの作成（スキーマはtransform.pyを参照）
```

### 6. Cloud Storageバケットの作成

```bash
gsutil mb -p $PROJECT_ID -l asia-northeast1 gs://your-bucket-name
```

## 環境変数

Cloud Functionに設定する環境変数：

| 変数名 | 説明 | 必須 | デフォルト |
|--------|------|------|-----------|
| `PROJECT_ID` | GCPプロジェクトID | ✅ | - |
| `BUCKET_NAME` | Cloud Storageバケット名 | ✅ | - |
| `BQ_DATASET` | BigQueryデータセット名 | ❌ | `rakuten_orders` |
| `BQ_TABLE_ORDERS` | BigQuery注文テーブル名 | ❌ | `orders` |
| `BQ_TABLE_ORDER_ITEMS` | BigQuery注文アイテムテーブル名 | ❌ | `order_items` |
| `BQ_LOCATION` | BigQueryロケーション | ❌ | - |
| `STRICT_RAW_PER_BATCH` | API呼び出し単位でRaw保存 | ❌ | `false` |
| `RAKUTEN_SERVICE_SECRET_ID` | Secret ManagerのシークレットID | ❌ | `rakuten-service-secret` |
| `RAKUTEN_LICENSE_KEY_ID` | Secret ManagerのライセンスキーID | ❌ | `rakuten-license-key` |

## デプロイ

### Cloud Functionのデプロイ

```bash
gcloud functions deploy rakuten-etl \
  --gen2 \
  --runtime=python311 \
  --region=asia-northeast1 \
  --source=. \
  --entry-point=main \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars="PROJECT_ID=your-project-id,BUCKET_NAME=your-bucket-name" \
  --timeout=540s \
  --memory=512MB
```

## 使用方法

### 実行モード

Cloud Functionは以下の3つのモードをサポートしています：

#### 1. MONTHLY（デフォルト）

前月分のデータを取得します。

```bash
curl "https://YOUR-FUNCTION-URL?mode=MONTHLY"
```

#### 2. CUSTOM

指定期間のデータを取得します。

```bash
curl "https://YOUR-FUNCTION-URL?mode=CUSTOM&start=2024-01-01&end=2024-01-31"
```

#### 3. HISTORICAL

過去730日分（約24ヶ月）のデータを取得します。

```bash
curl "https://YOUR-FUNCTION-URL?mode=HISTORICAL"
```

⚠️ **注意**: HISTORICALモードは大量データ処理には非推奨です。Cloud Functionsのタイムアウト（最大540秒）のリスクがあります。大量データの取り込みには、Cloud Tasks + CUSTOMモードの使用を推奨します。

### その他のオプション

#### DRY RUN

データの取得件数のみを確認（GCS/BigQueryへの書き込みは行いません）。

```bash
curl "https://YOUR-FUNCTION-URL?mode=CUSTOM&start=2024-01-01&end=2024-01-31&dry_run=1"
```

### 過去データの一括取り込み

Cloud Tasksを使用して月ごとに分割実行する方法：

詳細は [DEPLOY_HISTORICAL.md](./DEPLOY_HISTORICAL.md) を参照してください。

```bash
# 環境変数の設定
export PROJECT_ID="your-project-id"
export LOCATION="asia-northeast1"
export QUEUE_NAME="rakuten-historical"
export FUNCTION_URL="https://YOUR-FUNCTION-URL"

# DRY RUNで確認
python deploy_historical_tasks.py \
  --start-date 2022-01-01 \
  --end-date 2024-01-01 \
  --dry-run

# 実際にタスクを作成
python deploy_historical_tasks.py \
  --start-date 2022-01-01 \
  --end-date 2024-01-01
```

### 定期実行の設定

Cloud Schedulerを使用して月次実行を設定：

```bash
gcloud scheduler jobs create http rakuten-monthly-etl \
  --location=asia-northeast1 \
  --schedule="0 2 1 * *" \
  --uri="https://YOUR-FUNCTION-URL?mode=MONTHLY" \
  --http-method=GET \
  --time-zone="Asia/Tokyo"
```

## プロジェクト構成

```
rakuten-bq-pipeline/
├── main.py                    # Cloud Functionエントリーポイント
├── rakuten_client.py          # 楽天RMS APIクライアント
├── storage_client.py          # Cloud Storageへの保存
├── bigquery_client.py         # BigQueryへの書き込み
├── transform.py               # データ正規化
├── utils.py                   # Secret Manager / Logging設定
├── deploy_historical_tasks.py # 過去データ取り込みスクリプト
├── requirements.txt           # Python依存関係
├── README.md                  # このファイル
└── DEPLOY_HISTORICAL.md       # 過去データ取り込みガイド
```

## データフロー

### 1. データ取得

`rakuten_client.py`が楽天RMS APIから注文データを取得：
- `searchOrder`: 指定期間の注文番号リストを取得
- `getOrder`: 注文番号から注文詳細を取得

### 2. Raw保存

`storage_client.py`が取得したデータをCloud Storageに保存：
- パス: `raw/YYYY/MM/getOrder_YYYYMMDD_HHMMSS.json`
- 形式: JSON（日本語可読）

### 3. データ正規化

`transform.py`が注文データを正規化：
- `orders`: 注文ヘッダー情報
- `order_items`: 注文アイテム情報

### 4. BigQuery投入

`bigquery_client.py`が正規化データをBigQueryに投入：
- 月単位で完全更新（削除→挿入）
- パーティション: なし（必要に応じて追加可能）

## BigQueryスキーマ

### orders テーブル

| カラム名 | 型 | 説明 |
|---------|-----|------|
| `order_number` | STRING | 注文番号 |
| `order_datetime` | TIMESTAMP | 注文日時 |
| `order_status` | STRING | 注文ステータス |
| `total_price` | FLOAT | 合計金額 |
| `goods_price` | FLOAT | 商品金額 |
| `postage_price` | FLOAT | 送料 |
| `payment_method` | STRING | 支払い方法 |
| `delivery_name` | STRING | 配送方法名 |
| `user_email` | STRING | ユーザーEmail |
| `prefecture` | STRING | 都道府県 |
| `inserted_at` | TIMESTAMP | 取り込み日時 |

### order_items テーブル

| カラム名 | 型 | 説明 |
|---------|-----|------|
| `order_number` | STRING | 注文番号 |
| `basket_id` | STRING | バスケットID |
| `item_id` | STRING | 商品ID |
| `item_name` | STRING | 商品名 |
| `price` | FLOAT | 単価（税抜） |
| `price_tax_incl` | FLOAT | 単価（税込） |
| `quantity` | INTEGER | 数量 |
| `subtotal` | FLOAT | 小計 |
| `tax_rate` | FLOAT | 税率 |
| `inserted_at` | TIMESTAMP | 取り込み日時 |

## トラブルシューティング

### エラー: Secret Managerから認証情報を取得できない

- Secret Managerにシークレットが作成されているか確認
- Cloud FunctionのサービスアカウントにSecret Managerへのアクセス権限があるか確認

```bash
# 権限の付与
gcloud secrets add-iam-policy-binding rakuten-service-secret \
  --member="serviceAccount:YOUR-SERVICE-ACCOUNT@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=$PROJECT_ID
```

### エラー: BigQueryへの書き込みに失敗

- BigQueryデータセットとテーブルが作成されているか確認
- Cloud FunctionのサービスアカウントにBigQueryへの書き込み権限があるか確認

### エラー: Cloud Storageへの書き込みに失敗

- バケットが作成されているか確認
- Cloud FunctionのサービスアカウントにStorageへの書き込み権限があるか確認

### タイムアウトエラー

- 大量データの処理にはCloud Tasks + CUSTOMモードを使用
- Cloud Functionのタイムアウト設定を確認（最大540秒）

### APIレート制限

- 楽天RMS APIのレート制限に注意
- Cloud Tasksの同時実行数を調整（`--max-concurrent-dispatches`）

## ローカル開発

### ローカルで実行

```bash
# 環境変数の設定
export PROJECT_ID="your-project-id"
export BUCKET_NAME="your-bucket-name"
export RAKUTEN_SERVICE_SECRET="your-secret"
export RAKUTEN_LICENSE_KEY="your-key"

# Functions Frameworkで実行
functions-framework --target=main --port=8080
```

### テスト

```bash
# DRY RUNでテスト
curl "http://localhost:8080?mode=CUSTOM&start=2024-01-01&end=2024-01-31&dry_run=1"
```

## セキュリティ

- 認証情報はSecret Managerで管理
- Cloud Functionは必要最小限の権限で実行
- HTTPS通信を使用
- 環境変数に機密情報を直接設定しない

## ライセンス

このプロジェクトのライセンス情報を記載してください。

## 貢献

プルリクエストやイシューの報告を歓迎します。

## 参考資料

- [RakutenPayOrderAPI ドキュメント](https://webservice.rms.rakuten.co.jp/merchant-portal/view/ja/common/1-1_service_index/rakutenpayorderapi/)
- [Google Cloud Functions ドキュメント](https://cloud.google.com/functions/docs)
- [BigQuery ドキュメント](https://cloud.google.com/bigquery/docs)

