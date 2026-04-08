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
  cloudtasks.googleapis.com \
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

### 4-1. 専用サービスアカウントの作成

Compute Engine デフォルト SA ではなく専用 SA を使うのが推奨です。

```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# 専用 SA を作成
gcloud iam service-accounts create cloud-build-trigger-deployer \
  --display-name="Cloud Build Trigger Deployer" \
  --project=$PROJECT_ID

SA="cloud-build-trigger-deployer@${PROJECT_ID}.iam.gserviceaccount.com"

# Cloud Functions デプロイ権限
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA}" \
  --role="roles/cloudfunctions.developer"

# Cloud Run 操作（Gen2 は Cloud Run ベース）
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA}" \
  --role="roles/run.admin"

# ランタイム SA への権限委任
gcloud iam service-accounts add-iam-policy-binding \
  "${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --member="serviceAccount:${SA}" \
  --role="roles/iam.serviceAccountUser"

# ビルドログ書き込み（cloudbuild.yaml に logging: CLOUD_LOGGING_ONLY を設定済みのため必要）
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA}" \
  --role="roles/logging.logWriter"

# ビルドソース GCS アップロード（ソースコードのアップロードに使用）
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA}" \
  --role="roles/storage.objectAdmin"
```

> **ログ出力について**: `cloudbuild.yaml` に `options: logging: CLOUD_LOGGING_ONLY` を設定しているため、ビルドログは Cloud Logging にのみ出力されます。GCS ログバケットへの権限付与は不要です。専用 SA でデフォルトの GCS ログバケットを使おうとすると権限エラーになるため、この設定が必要です。

### 4-2. トリガーの作成

GCP Console → Cloud Build → トリガー → 「トリガーを作成」

| 設定項目 | 値 |
|---------|---|
| 名前 | `rakuten-etl-deploy`（任意） |
| リージョン | `asia-northeast1`（第2世代リポジトリに必要） |
| イベント | ブランチへの push |
| ソース | GitHub（第2世代） |
| リポジトリ | `rakuten-bq-pipeline`（共通）またはフォーク先リポジトリ |
| ブランチ | `^main$` |
| 構成ファイルの種類 | Cloud Build 構成ファイル |
| Cloud Build 構成ファイルの場所 | `/cloudbuild.yaml` |
| サービスアカウント | `cloud-build-trigger-deployer@{PROJECT_ID}.iam.gserviceaccount.com` |

### 4-3. 動作確認

```bash
# 手動実行でテスト
gcloud builds triggers run "rakuten-etl-deploy" \
  --branch=main \
  --project=$PROJECT_ID \
  --region=asia-northeast1

# ビルド結果確認
gcloud builds list \
  --project=$PROJECT_ID \
  --region=asia-northeast1 \
  --limit=3 \
  --format="table(id,status,createTime,duration)"
```

以降は `main` への push で自動デプロイされます。手動の `gcloud functions deploy` は不要です。

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
  --timeout=3600s \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},BUCKET_NAME=${BUCKET_NAME},BQ_DATASET=rakuten_orders,BQ_LOCATION=asia-northeast1,SKIP_LTV_UPDATE=false,PRODUCT_MASTER_SHEET_ID={SPREADSHEET_ID},PRODUCT_MASTER_SHEET_RANGE=ASIN_List!B:E" \
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
>
> **`PRODUCT_MASTER_SHEET_RANGE`** は `タブ名!列範囲` の形式で指定します。タブ名を省略して `B:E` のみにすると**最初のタブを自動取得**します。

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

Cloud Tasks を使って過去2年分の注文データを月ごとに分割して取り込みます。
詳細手順は `DEPLOY_HISTORICAL.md` を参照してください。

```bash
cd ~/rakuten-bq-pipeline

# ドライランで取り込み対象を確認
python deploy_historical_tasks.py --dry-run

# タスクを登録して実行
python deploy_historical_tasks.py
```

全タスク完了後、LTV テーブルの初期データを投入します：

```bash
PROJECT_ID=$PROJECT_ID python initialize_ltv_tables.py
```

---

## Step 12：Cloud Schedulerの設定（月次自動実行）

```bash
FUNCTION_URL="https://asia-northeast1-${PROJECT_ID}.cloudfunctions.net/rakuten-etl"

# 毎月1日 午前9時（JST）に自動実行
# --max-retries=0: リトライなし（並列実行・リトライ地獄を防ぐ）
# --attempt-deadline=30m: 接続待機を最大限延ばす
gcloud scheduler jobs create http rakuten-monthly-etl \
  --location=asia-northeast1 \
  --schedule="0 9 1 * *" \
  --uri="${FUNCTION_URL}?mode=MONTHLY" \
  --http-method=GET \
  --time-zone="Asia/Tokyo" \
  --max-retries=0 \
  --attempt-deadline=30m \
  --project=$PROJECT_ID
```

> **タイムアウトについて**: 注文件数が多い月は処理が 30 分を超え Cloud Scheduler に 504 が返ることがありますが、Cloud Function 自体は最大 60 分（3600 秒）動き続けて処理を完走します。`--max-retries=0` により再実行は起きません。

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

## Appendix：月次処理のアーキテクチャ移行パス

> **現状構成の制約と、問題が出た場合の対応策をまとめたメモ。**

### 現状構成

```
Cloud Scheduler (月1回) → HTTP GET → rakuten-etl (Cloud Functions Gen2, 最大60分)
```

| 設定 | 値 | 理由 |
|------|---|------|
| `--timeout` | `3600s` | 注文件数が多い月でも完走できるよう最大値 |
| `--max-retries` | `0` | 504 後の再実行・並列実行を防ぐ |
| `--attempt-deadline` | `30m` | Scheduler 側の最大接続待機 |

**GCS 実行ロック**（`locks/monthly-YYYY-MM.lock`）がコードに組み込み済み。  
同一月に対して 2 本目の実行が来ても自動でスキップされる。

### 問題が出るとすればどんな場合？

- 注文件数がさらに増え、1ヶ月分の処理が **60分を超える**ようになった場合
- Scheduler の 504 → ロック未取得前に並列起動した場合（起動直後の競合）
- Cloud Functions の **コールドスタート + メモリ不足** でのクラッシュが頻発する場合

### 次のアーキテクチャ案：Cloud Run Jobs

Cloud Functions の HTTP タイムアウト制約を根本から取り除く方法。

```
Cloud Scheduler (月1回) → Cloud Run Jobs (コンテナ, 最大24時間)
```

**移行に必要な主な作業：**

1. `Dockerfile` の作成（既存の Python コードをそのまま使える）
2. `main.py` の `main_endpoint()` をスクリプトのエントリーポイントに変更（Flask 不要）
3. Cloud Run Jobs のデプロイ設定（`gcloud run jobs create`）
4. Cloud Scheduler のターゲットを Cloud Run Jobs 実行 API に変更

```bash
# Cloud Run Jobs の作成例（参考）
gcloud run jobs create rakuten-monthly-job \
  --image=asia-northeast1-docker.pkg.dev/${PROJECT_ID}/rakuten/etl:latest \
  --region=asia-northeast1 \
  --task-count=1 \
  --max-retries=0 \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},..." \
  --project=$PROJECT_ID

# Scheduler から Jobs を起動する例
gcloud scheduler jobs create http rakuten-monthly-job-trigger \
  --location=asia-northeast1 \
  --schedule="0 9 1 * *" \
  --uri="https://run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/rakuten-monthly-job:run" \
  --http-method=POST \
  --oauth-service-account-email="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --time-zone="Asia/Tokyo" \
  --max-retries=0 \
  --project=$PROJECT_ID
```

> Cloud Run Jobs は実行完了が HTTP 応答ではなくジョブ終了で判定されるため、  
> タイムアウト問題・状態不明問題・並列実行問題がすべて解消される。

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
