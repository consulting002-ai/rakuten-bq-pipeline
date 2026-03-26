# 過去データ取り込みガイド

Cloud Tasks を使用して過去データを月ごとに分割して取り込む手順です。
1ヶ月分ずつ個別の Cloud Function 呼び出しとしてキューに登録するため、タイムアウトの心配がありません。

## 前提条件

- Cloud Function (`rakuten-etl`) がデプロイ済みであること
- Cloud Shell で `PROJECT_ID` / `FUNCTION_URL` 環境変数が設定済みであること

---

## Step 1：Cloud Tasks API を有効化

```bash
gcloud services enable cloudtasks.googleapis.com --project=$PROJECT_ID
```

---

## Step 2：ドライランで確認（タスクは作成されない）

```bash
cd ~/rakuten-bq-pipeline

python deploy_historical_tasks.py --dry-run
```

過去24ヶ月分のタスク一覧が表示されます。期間を絞りたい場合：

```bash
python deploy_historical_tasks.py \
  --start-date 2024-01-01 \
  --end-date 2026-01-01 \
  --dry-run
```

---

## Step 3：タスクを登録して実行

```bash
# 過去24ヶ月分（デフォルト）
python deploy_historical_tasks.py

# 期間を指定する場合
python deploy_historical_tasks.py \
  --start-date 2024-01-01 \
  --end-date 2026-01-01
```

タスクが登録されると Cloud Tasks キューが月ごとの処理を順次実行します。

> **同時実行数を絞りたい場合**: Rakuten API のレート制限が気になる場合は `--max-concurrent-dispatches` で同時実行数を下げてください。
>
> ```bash
> python deploy_historical_tasks.py --max-concurrent-dispatches 3
> ```

---

## 進捗確認

### Cloud Console で確認

1. [Cloud Tasks コンソール](https://console.cloud.google.com/cloudtasks)を開く
2. プロジェクトを選択
3. キュー `rakuten-historical` を選択してタスクの状態を確認

### コマンドラインで確認

```bash
QUEUE_NAME="rakuten-historical"

# キューの一覧
gcloud tasks queues list --location=asia-northeast1 --project=$PROJECT_ID

# タスクの一覧
gcloud tasks list --queue=$QUEUE_NAME --location=asia-northeast1 --project=$PROJECT_ID
```

---

## 特定の月だけ再実行したい場合

```bash
python deploy_historical_tasks.py \
  --start-date 2024-06-01 \
  --end-date 2024-06-30
```

---

## キューをリセットしたい場合

```bash
QUEUE_NAME="rakuten-historical"

# キュー内の全タスクを削除
gcloud tasks queues purge $QUEUE_NAME --location=asia-northeast1 --project=$PROJECT_ID
```

---

## オプション一覧

| オプション | デフォルト | 説明 |
|---|---|---|
| `--start-date` | 24ヶ月前 | 開始日（YYYY-MM-DD） |
| `--end-date` | 今日 | 終了日（YYYY-MM-DD） |
| `--dry-run` | false | タスク一覧の確認のみ（登録しない） |
| `--max-concurrent-dispatches` | 3 | 同時実行数の上限 |

> **同時実行数について**: デフォルトの10で問題ありません。上げすぎると Rakuten API のレート制限に引っかかる可能性があります。

---

## 完了確認

全タスクが完了したら BigQuery でデータを確認します：

```sql
SELECT
  FORMAT_TIMESTAMP('%Y-%m', order_datetime, 'Asia/Tokyo') AS month,
  COUNT(*) AS order_count
FROM `{PROJECT_ID}.rakuten_orders.orders`
GROUP BY month
ORDER BY month
```
