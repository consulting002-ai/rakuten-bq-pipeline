#!/usr/bin/env python3
"""
Cloud Tasksを使用して過去データの取り込みタスクを月ごとに生成するスクリプト

使用方法:
    # 環境変数を設定
    export PROJECT_ID="your-project-id"
    export LOCATION="asia-northeast1"
    export QUEUE_NAME="rakuten-historical"
    export FUNCTION_URL="https://YOUR-FUNCTION-URL"
    
    # スクリプト実行
    python deploy_historical_tasks.py --start-date 2022-01-01 --end-date 2024-01-01

オプション:
    --start-date: 開始日 (YYYY-MM-DD形式、デフォルト: 24ヶ月前)
    --end-date: 終了日 (YYYY-MM-DD形式、デフォルト: 今日)
    --dry-run: 実際にタスクを作成せず、作成されるタスクの一覧を表示
    --max-concurrent-dispatches: 同時実行数の上限（デフォルト: 10）
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional
from dateutil.relativedelta import relativedelta

from google.cloud import tasks_v2
from google.api_core import exceptions

from config import PROJECT_ID as _CONFIG_PROJECT_ID, BQ_LOCATION as LOCATION

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# スクリプト固有の設定
QUEUE_NAME = os.getenv("QUEUE_NAME", "rakuten-historical")
FUNCTION_URL = os.getenv("FUNCTION_URL")


def _resolve_project_id() -> str:
    """
    PROJECT_ID を解決する（環境変数 → gcloud のデフォルトプロジェクト の順）
    """
    if _CONFIG_PROJECT_ID:
        return _CONFIG_PROJECT_ID
    try:
        import subprocess
        project_id = subprocess.check_output(
            ["gcloud", "config", "get-value", "project"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if project_id and project_id != "(unset)":
            return project_id
    except Exception:
        pass
    return ""


PROJECT_ID = _resolve_project_id()

JST = ZoneInfo("Asia/Tokyo")


def month_start(dt: datetime) -> datetime:
    """dt（JST）の月初 00:00:00 JST を返す"""
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def next_month(dt: datetime) -> datetime:
    """次の月の月初を返す"""
    return (month_start(dt) + relativedelta(months=1))


def monthly_ranges_jst(start_dt: datetime, end_dt: datetime):
    """
    [start_dt, end_dt) をJSTの月境界で分割して yield (m_start, m_end)
    start_dt, end_dt は JST の aware datetime（end は開区間）
    """
    cur = month_start(start_dt)
    if cur < start_dt:
        cur = month_start(start_dt)
    while cur < end_dt:
        m_start = cur
        m_end = next_month(cur)
        if m_end > end_dt:
            m_end = end_dt
        yield (m_start, m_end)
        cur = next_month(cur)


def create_or_get_queue(
    client: tasks_v2.CloudTasksClient,
    project_id: str,
    location: str,
    queue_name: str,
    max_concurrent_dispatches: int = 10
) -> str:
    """
    Cloud Tasksキューを作成（既に存在する場合は取得）
    
    Returns:
        str: キューのパス
    """
    parent = f"projects/{project_id}/locations/{location}"
    queue_path = f"{parent}/queues/{queue_name}"
    
    # キューの設定
    queue = tasks_v2.Queue(
        name=queue_path,
        rate_limits=tasks_v2.RateLimits(
            max_dispatches_per_second=10,  # 秒あたりの最大ディスパッチ数
            max_concurrent_dispatches=max_concurrent_dispatches,  # 同時実行数
        ),
        retry_config=tasks_v2.RetryConfig(
            max_attempts=3,  # 最大リトライ回数
            max_retry_duration={"seconds": 3600},  # 最大リトライ時間（1時間）
            min_backoff={"seconds": 10},  # 最小バックオフ
            max_backoff={"seconds": 300},  # 最大バックオフ（5分）
        ),
    )
    
    try:
        # キューを作成
        response = client.create_queue(
            request={
                "parent": parent,
                "queue": queue,
            }
        )
        logger.info(f"✅ キューを作成しました: {queue_name}")
        return response.name
    except exceptions.AlreadyExists:
        logger.info(f"ℹ️  キューは既に存在します: {queue_name}")
        return queue_path
    except Exception as e:
        logger.error(f"❌ キューの作成に失敗しました: {e}")
        raise


def create_monthly_tasks(
    client: tasks_v2.CloudTasksClient,
    queue_path: str,
    function_url: str,
    start_date: datetime,
    end_date: datetime,
    dry_run: bool = False
) -> int:
    """
    月ごとにCloud Tasksを作成
    
    Returns:
        int: 作成したタスク数
    """
    task_count = 0
    tasks_info = []
    
    for m_start, m_end in monthly_ranges_jst(start_date, end_date):
        # end_dateは開区間なので、前日までを含める
        month_end_str = (m_end - timedelta(days=1)).strftime("%Y-%m-%d")
        month_start_str = m_start.strftime("%Y-%m-%d")
        
        # HTTPリクエストのURL
        url = f"{function_url}?mode=CUSTOM&start={month_start_str}&end={month_end_str}"
        
        # タスクの作成
        # dispatch_deadline: Cloud Tasks が HTTP レスポンスを待つ最大時間（最大 30 分）
        # 1 ヶ月分の getOrder は最大 ~150 回 API 呼び出しになるため余裕を持って 30 分に設定
        task = tasks_v2.Task(
            http_request=tasks_v2.HttpRequest(
                http_method=tasks_v2.HttpMethod.GET,
                url=url,
                headers={"Content-Type": "application/json"},
            ),
            dispatch_deadline={"seconds": 1800},  # 30 分
        )
        
        tasks_info.append({
            "month": m_start.strftime("%Y-%m"),
            "start": month_start_str,
            "end": month_end_str,
            "url": url,
        })
        
        if not dry_run:
            try:
                response = client.create_task(
                    request={"parent": queue_path, "task": task}
                )
                logger.info(
                    f"✅ タスクを作成: {m_start.strftime('%Y-%m')} "
                    f"({month_start_str} 〜 {month_end_str}) -> {response.name.split('/')[-1]}"
                )
                task_count += 1
            except Exception as e:
                logger.error(
                    f"❌ タスクの作成に失敗: {m_start.strftime('%Y-%m')} - {e}"
                )
        else:
            logger.info(
                f"📋 [DRY RUN] タスク: {m_start.strftime('%Y-%m')} "
                f"({month_start_str} 〜 {month_end_str})"
            )
            task_count += 1
    
    if dry_run:
        logger.info("\n=== DRY RUN: 作成されるタスク一覧 ===")
        for info in tasks_info:
            logger.info(f"  {info['month']}: {info['start']} 〜 {info['end']}")
        logger.info(f"\n合計: {task_count}個のタスクが作成されます")
    
    return task_count


def main():
    parser = argparse.ArgumentParser(
        description="過去データ取り込み用のCloud Tasksを月ごとに生成"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="開始日 (YYYY-MM-DD形式)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="終了日 (YYYY-MM-DD形式)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="実際にタスクを作成せず、作成されるタスクの一覧を表示",
    )
    parser.add_argument(
        "--max-concurrent-dispatches",
        type=int,
        default=3,
        help="同時実行数の上限（デフォルト: 3）",
    )
    parser.add_argument(
        "--purge-queue",
        action="store_true",
        help="タスク追加の前にキュー内の未処理タスクをすべて削除する",
    )

    args = parser.parse_args()
    
    # PROJECT_ID の確認
    if not PROJECT_ID:
        logger.error("❌ PROJECT_ID を解決できません。`gcloud config set project PROJECT_ID` を実行してください")
        sys.exit(1)

    # FUNCTION_URL の解決（環境変数 → PROJECT_ID から自動生成 の順）
    function_url = FUNCTION_URL
    if not function_url:
        function_url = f"https://asia-northeast1-{PROJECT_ID}.cloudfunctions.net/rakuten-etl"
        logger.info(f"ℹ️  FUNCTION_URL が未設定のため自動生成: {function_url}")
    
    # 日付の設定
    now_jst = datetime.now(JST)
    
    if args.end_date:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d").replace(tzinfo=JST)
    else:
        end_date = now_jst
    
    if args.start_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d").replace(tzinfo=JST)
    else:
        # デフォルト: 24ヶ月前
        start_date = (now_jst - relativedelta(months=24)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # 日付の検証
    if start_date >= end_date:
        logger.error("❌ 開始日は終了日より前である必要があります")
        sys.exit(1)
    
    logger.info(f"📅 期間: {start_date.strftime('%Y-%m-%d')} 〜 {end_date.strftime('%Y-%m-%d')}")
    logger.info(f"🔧 プロジェクト: {PROJECT_ID}")
    logger.info(f"📍 ロケーション: {LOCATION}")
    logger.info(f"📬 キュー名: {QUEUE_NAME}")
    logger.info(f"🔗 関数URL: {function_url}")
    if args.dry_run:
        logger.info("🔍 DRY RUN モード: タスクは作成されません")
    logger.info("")
    
    try:
        # Cloud Tasksクライアントの初期化
        client = tasks_v2.CloudTasksClient()
        
        # キューの作成/取得
        queue_path = create_or_get_queue(
            client=client,
            project_id=PROJECT_ID,
            location=LOCATION,
            queue_name=QUEUE_NAME,
            max_concurrent_dispatches=args.max_concurrent_dispatches,
        )

        # --purge-queue: 未処理タスクを全削除してからタスクを再投入する
        if args.purge_queue and not args.dry_run:
            logger.info(f"🗑️  キューをパージします: {QUEUE_NAME}")
            client.purge_queue(request={"name": queue_path})
            logger.info("✅ パージ完了")

        # タスクの作成
        task_count = create_monthly_tasks(
            client=client,
            queue_path=queue_path,
            function_url=function_url,
            start_date=start_date,
            end_date=end_date,
            dry_run=args.dry_run,
        )
        
        if not args.dry_run:
            logger.info(f"\n✅ 完了: {task_count}個のタスクを作成しました")
            logger.info(f"📊 キューの状態を確認: https://console.cloud.google.com/cloudtasks/queue/{LOCATION}/{QUEUE_NAME}?project={PROJECT_ID}")
        else:
            logger.info(f"\n✅ DRY RUN完了: {task_count}個のタスクが作成される予定です")
        
    except Exception as e:
        logger.exception(f"❌ エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

