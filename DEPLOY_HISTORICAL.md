# 過去データ取り込みガイド

Cloud Tasksを使用して過去データを月ごとに取り込む方法を説明します。

## 前提条件

1. Cloud Functionがデプロイ済みであること
2. Cloud Tasks APIが有効になっていること
3. 必要な権限があること（Cloud Tasks Admin）

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

```bash
export PROJECT_ID="your-project-id"
export LOCATION="asia-northeast1"  # デフォルト: asia-northeast1
export QUEUE_NAME="rakuten-historical"  # デフォルト: rakuten-historical
export FUNCTION_URL="https://YOUR-REGION-YOUR-PROJECT.cloudfunctions.net/your-function-name"
```

### 3. Cloud Tasks APIの有効化

```bash
gcloud services enable cloudtasks.googleapis.com --project=$PROJECT_ID
```

## 使用方法

### 基本的な使い方

#### 1. まずはDRY RUNで確認

```bash
python deploy_historical_tasks.py \
  --start-date 2022-01-01 \
  --end-date 2024-01-01 \
  --dry-run
```

これにより、作成されるタスクの一覧が表示されます（実際にはタスクは作成されません）。

#### 2. 実際にタスクを作成

```bash
python deploy_historical_tasks.py \
  --start-date 2022-01-01 \
  --end-date 2024-01-01
```

#### 3. デフォルト設定で実行（過去24ヶ月分）

```bash
python deploy_historical_tasks.py
```

### オプション

- `--start-date`: 開始日 (YYYY-MM-DD形式、デフォルト: 24ヶ月前)
- `--end-date`: 終了日 (YYYY-MM-DD形式、デフォルト: 今日)
- `--dry-run`: 実際にタスクを作成せず、作成されるタスクの一覧を表示
- `--max-concurrent-dispatches`: 同時実行数の上限（デフォルト: 10）

### 例: 同時実行数を調整

```bash
python deploy_historical_tasks.py \
  --start-date 2022-01-01 \
  --end-date 2024-01-01 \
  --max-concurrent-dispatches 5
```

## キューの設定

スクリプトは自動的にCloud Tasksキューを作成します。設定内容：

- **同時実行数**: デフォルト10（`--max-concurrent-dispatches`で変更可能）
- **リトライ設定**:
  - 最大リトライ回数: 3回
  - 最大リトライ時間: 1時間
  - バックオフ: 10秒〜5分

## タスクの監視

### Cloud Consoleで確認

1. [Cloud Tasks Console](https://console.cloud.google.com/cloudtasks)にアクセス
2. プロジェクトとロケーションを選択
3. キュー名（デフォルト: `rakuten-historical`）を選択
4. タスクの状態を確認

### コマンドラインで確認

```bash
# キューの一覧
gcloud tasks queues list --location=$LOCATION --project=$PROJECT_ID

# タスクの一覧
gcloud tasks list --queue=$QUEUE_NAME --location=$LOCATION --project=$PROJECT_ID

# タスクの詳細
gcloud tasks describe TASK_NAME --queue=$QUEUE_NAME --location=$LOCATION --project=$PROJECT_ID
```

## トラブルシューティング

### タスクが実行されない

1. Cloud FunctionのURLが正しいか確認
2. Cloud Functionに必要な権限があるか確認
3. キューの設定を確認（同時実行数など）

### 特定の月だけ再実行したい

失敗したタスクのみ再実行する場合：

```bash
# 特定の月のタスクを再作成
python deploy_historical_tasks.py \
  --start-date 2023-06-01 \
  --end-date 2023-06-30
```

### タスクを削除したい

```bash
# キュー内の全タスクを削除
gcloud tasks queues purge $QUEUE_NAME --location=$LOCATION --project=$PROJECT_ID

# 特定のタスクを削除
gcloud tasks delete TASK_NAME --queue=$QUEUE_NAME --location=$LOCATION --project=$PROJECT_ID
```

## 注意事項

1. **APIレート制限**: Rakuten APIのレート制限に注意してください
2. **コスト**: Cloud Tasksの使用量に応じて課金されます
3. **タイムアウト**: Cloud Functionのタイムアウト設定を確認してください
4. **並列実行**: 同時実行数を上げすぎると、APIレート制限に引っかかる可能性があります

## 実行例

### 例1: 過去2年分を一括取り込み

```bash
export PROJECT_ID="my-project"
export FUNCTION_URL="https://asia-northeast1-my-project.cloudfunctions.net/rakuten-etl"

python deploy_historical_tasks.py \
  --start-date 2022-01-01 \
  --end-date 2024-01-01
```

### 例2: 特定の期間のみ（テスト用）

```bash
python deploy_historical_tasks.py \
  --start-date 2023-12-01 \
  --end-date 2023-12-31 \
  --dry-run
```

## 次のステップ

1. タスクの実行状況を監視
2. Cloud Loggingでログを確認
3. BigQueryでデータが正しく取り込まれているか確認
4. 定期的な実行はCloud Schedulerで設定（MONTHLYモードを使用）

