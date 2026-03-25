# 新ショップ追加手順書

このリポジトリをテンプレートとして、新しいショップのLTVパイプラインを構築する手順です。

## 前提条件

- GCP組織の管理者権限（Googleアカウントでログイン済み）
- 楽天RMS API の SERVICE_SECRET / LICENSE_KEY を入手済み
- Googleスプレッドシートで商品マスタを用意済み

> **CLIはすべて Cloud Shell から実行します。**
> GCP Console 右上の `>_` アイコンから起動してください。
> gcloud は認証済みの状態で起動するため、ログイン作業は不要です。

---

## プロジェクトIDの命名規則

このドキュメントでは GCP プロジェクト ID 全体を `{PROJECT_ID}` と表記します。
用途に応じて以下のように命名してください：

| 用途 | 命名例 |
|------|--------|
| 開発・検証 | `{SHOP_ID}-ltv-dev` |
| 本番 | `{SHOP_ID}-ltv` |
| 本番（リリース日付付き） | `{SHOP_ID}-ltv-20260401` |

GCS バケット名は `{PROJECT_ID}-raw-jsons` を推奨します（例：`{SHOP_ID}-ltv-raw-jsons`）。

---

## Step 1：GCPプロジェクトの作成

```bash
# PROJECT_ID を変数に設定（以降のコマンドで使い回す）
PROJECT_ID="{SHOP_ID}-ltv"   # ← {SHOP_ID} を実際のショップIDに変更してください（例: smarttanpaku-ltv）

# プロジェクトを作成（プロジェクトIDは世界で一意である必要があります）
gcloud projects create $PROJECT_ID --name="{ショップ名} LTV"

# 請求アカウントを紐付け（請求アカウントIDは GCP Console → お支払い で確認）
gcloud billing projects link $PROJECT_ID \
  --billing-account=XXXXXX-XXXXXX-XXXXXX

# プロジェクトを設定
gcloud config set project $PROJECT_ID
```

---

## Step 2：必要なAPIを有効化

```bash
gcloud services enable \
  cloudfunctions.googleapis.com \
  cloudbuild.googleapis.com \
  bigquery.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com \
  cloudscheduler.googleapis.com \
  sheets.googleapis.com \
  run.googleapis.com \
  --project=$PROJECT_ID
```

---

## Step 3：Cloud Build Trigger から自動デプロイされるリポジトリをクローン

Cloud Shell でリポジトリをクローンします（Step 7 の初回デプロイと bootstrap.py の実行に使用）：

```bash
git clone https://github.com/consulting002-ai/rakuten-bq-pipeline.git
cd rakuten-bq-pipeline
pip install -r requirements.txt
```

> **カスタムコードが必要な場合のみ** `rakuten-bq-pipeline` をフォークして独自リポジトリを作成し、
> Step 4 で参照リポジトリをフォーク先に変更してください。通常は共通リポジトリをそのまま使います。

---

## Step 4：Cloud Build Triggerの設定（GitHub連携・自動デプロイ）

GCP Console → Cloud Build → トリガー → 「トリガーを作成」

| 設定項目 | 値 |
|---------|---|
| ソース | GitHub（第2世代）|
| リポジトリ | `rakuten-bq-pipeline`（共通）またはフォーク先リポジトリ |
| ブランチ | `^main$` |
| 構成ファイル | `cloudbuild.yaml` |

Cloud Build のサービスアカウントに以下の権限を付与します：

```bash
# Cloud Build のサービスアカウントを確認
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.role=roles/cloudbuild.builds.builder" \
  --format="value(bindings.members)"

# 権限を付与（SA_EMAIL は上記コマンドで確認したアドレス）
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:{SA_EMAIL}" \
  --role="roles/cloudfunctions.developer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:{SA_EMAIL}" \
  --role="roles/iam.serviceAccountUser"
```

---

## Step 5：楽天APIキーを Secret Manager に登録

```bash
# Secretを作成
gcloud secrets create rakuten-service-secret --project=$PROJECT_ID
gcloud secrets create rakuten-license-key    --project=$PROJECT_ID

# 値を登録（入力内容は画面に表示されません）
read -s -p "SERVICE_SECRET を入力: " SVC_SECRET && echo
echo -n "$SVC_SECRET" | gcloud secrets versions add rakuten-service-secret \
  --data-file=- --project=$PROJECT_ID

read -s -p "LICENSE_KEY を入力: " LIC_KEY && echo
echo -n "$LIC_KEY" | gcloud secrets versions add rakuten-license-key \
  --data-file=- --project=$PROJECT_ID
```

> **serviceSecret は変わりません。** ライセンスキーは90日ごとに楽天RMSで再発行が必要です。
> 更新は `rakuten-admin` の `/update-license-key` ページから行います（Step 8参照）。

---

## Step 6：Chatwork通知用の Secret を登録

`rakuten-admin` からライセンスキー更新時の通知に使います。

```bash
# Secretを作成
gcloud secrets create chatwork-api-token --project=$PROJECT_ID
gcloud secrets create chatwork-room-id   --project=$PROJECT_ID

# Chatwork APIトークンを登録（ChatworkのマイページAPIトークンから取得）
read -s -p "Chatwork API Token を入力: " CW_TOKEN && echo
echo -n "$CW_TOKEN" | gcloud secrets versions add chatwork-api-token \
  --data-file=- --project=$PROJECT_ID

# 通知先ルームIDを登録（ChatworkのルームURL末尾の数字）
read -p "Chatwork Room ID を入力: " CW_ROOM
echo -n "$CW_ROOM" | gcloud secrets versions add chatwork-room-id \
  --data-file=- --project=$PROJECT_ID
```

---

## Step 7：Cloud Function サービスアカウントへの権限付与

Cloud Functions Gen2 は Compute Engine のデフォルトサービスアカウントで実行されます。
以下の権限を付与します。

```bash
# Compute Engine デフォルト SA のメールアドレスを取得
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
SA_EMAIL="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
echo $SA_EMAIL
```

### 7-1. Secret Manager へのアクセス権

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor"
```

### 7-2. Google スプレッドシートへのアクセス権

商品マスタのスプレッドシートをサービスアカウントと共有します。
GCP Console ではなく **Google スプレッドシート側** で設定します。

1. 対象のスプレッドシートを開く
2. 右上の「共有」ボタンをクリック
3. 上記の `SA_EMAIL`（`{PROJECT_NUMBER}-compute@developer.gserviceaccount.com`）を追加
4. 権限は「**閲覧者**」でOK
5. 「送信」をクリック

---

## Step 8：Cloud Functionの初回デプロイ（環境変数のセット）

**Cloud Build Trigger は環境変数を更新しません。** 初回のみ以下のコマンドで環境変数を込みでデプロイします。
Step 3 でクローンしたリポジトリのディレクトリ内で実行してください。

### 8-1. ETL本体（rakuten-etl）

```bash
BUCKET_NAME="${PROJECT_ID}-raw-jsons"

gcloud functions deploy rakuten-etl \
  --gen2 \
  --runtime=python311 \
  --region=asia-northeast1 \
  --source=. \
  --entry-point=main \
  --trigger-http \
  --allow-unauthenticated \
  --memory=2GiB \
  --timeout=540s \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},BUCKET_NAME=${BUCKET_NAME},BQ_DATASET=rakuten_orders,BQ_LOCATION=asia-northeast1,SKIP_LTV_UPDATE=false,PRODUCT_MASTER_SHEET_ID={SPREADSHEET_ID},PRODUCT_MASTER_SHEET_RANGE='シート1'!B:E" \
  --project=$PROJECT_ID
```

### 8-2. 管理機能（rakuten-admin）

ライセンスキー更新ページを公開エンドポイントとしてデプロイします。
アクセス制御はフォーム上の「現在のライセンスキー」による本人確認で行います。

```bash
gcloud functions deploy rakuten-admin \
  --gen2 \
  --runtime=python311 \
  --region=asia-northeast1 \
  --source=. \
  --entry-point=admin \
  --trigger-http \
  --allow-unauthenticated \
  --memory=256Mi \
  --timeout=60s \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},SHOP_NAME={ショップ表示名}" \
  --project=$PROJECT_ID
```

> **`{SPREADSHEET_ID}`** はGoogleスプレッドシートのURLに含まれるID（`/d/` と `/edit` の間の文字列）。

> **2回目以降のデプロイ**は GitHub への push → Cloud Build が自動実行します。環境変数はそのまま保持されます。

---

## Step 9：ライセンスキー更新ページの確認

ライセンスキー更新ページは認証不要の公開エンドポイントです。
フォームで「現在のライセンスキー」を入力することで本人確認を行います。

> **ライセンスキー更新ページの URL**：
> `https://asia-northeast1-{PROJECT_ID}.cloudfunctions.net/rakuten-admin/update-license-key`
>
> このURLを担当者に案内してください。URLは外部に漏れないよう管理してください。

**動作確認：**

1. 上記 URL をブラウザで開く
2. フォームが表示されることを確認
3. 現在のライセンスキーを誤入力 → 「現在のライセンスキーが正しくありません。」が表示されること
4. 現在のライセンスキーを正しく入力 → 「✅ ライセンスキーを更新しました」が表示されること

---

## Step 10：BigQueryデータセット・テーブルおよびGCSバケットの作成

Cloud Shell で実行します（Step 3 のリポジトリディレクトリ内）。

```bash
# 環境変数を設定して bootstrap.py を実行（データセット・全テーブル・GCSバケットを一括作成）
BUCKET_NAME="${PROJECT_ID}-raw-jsons"

PROJECT_ID=$PROJECT_ID \
  BUCKET_NAME=$BUCKET_NAME \
  python bootstrap.py
```

既に存在するリソースは自動的にスキップされます。

---

## Step 11：過去データの投入

`DEPLOY_HISTORICAL.md` を参照して、過去2年分の注文データを取り込みます。

```bash
# LTVテーブルの初期データを投入
PROJECT_ID=$PROJECT_ID python initialize_ltv_tables.py
```

---

## Step 12：Cloud Schedulerの設定（月次自動実行）

```bash
# 関数のURLを確認
gcloud functions describe rakuten-etl \
  --region=asia-northeast1 \
  --gen2 \
  --format="value(serviceConfig.uri)" \
  --project=$PROJECT_ID

# 毎月1日 午前2時（JST）に自動実行
gcloud scheduler jobs create http rakuten-monthly-etl \
  --location=asia-northeast1 \
  --schedule="0 2 1 * *" \
  --uri="{FUNCTION_URL}?mode=MONTHLY" \
  --http-method=GET \
  --time-zone="Asia/Tokyo" \
  --project=$PROJECT_ID
```

---

## Step 13：動作確認

```bash
FUNCTION_URL="https://asia-northeast1-${PROJECT_ID}.cloudfunctions.net/rakuten-etl"

# DRY RUN（データ書き込みなし）
curl "$FUNCTION_URL?mode=MONTHLY&dry_run=1"

# 本番実行
curl "$FUNCTION_URL?mode=MONTHLY"
```

**確認チェックリスト**
- [ ] Cloud Function がデプロイされている（`status: ACTIVE`）
- [ ] DRY RUN が成功する（HTTP 200）
- [ ] BigQuery に注文データが入っている
- [ ] LTVテーブルが更新されている
- [ ] Cloud Storage に Raw JSON が保存されている
- [ ] Cloud Scheduler が設定されている
- [ ] `rakuten-admin` のライセンスキー更新ページにアクセスできる

---

## 設定値メモ（ショップごとに記入）

| 項目 | 値 |
|------|---|
| SHOP_ID | |
| PROJECT_ID（GCPプロジェクトID） | |
| SHOP_NAME（表示名） | |
| BUCKET_NAME（GCSバケット） | |
| BQ_DATASET | `rakuten_orders` |
| スプレッドシートID | |
| Cloud Function URL（rakuten-etl） | |
| ライセンスキー更新URL（rakuten-admin） | |
| GitHubリポジトリ | |
