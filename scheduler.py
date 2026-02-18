"""
APScheduler 기반 매일 오전 7시 자동 실행 스케줄러
실행: python scheduler.py
"""
import logging
import sys
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

import main

# ── 로깅 ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def daily_job():
    """매일 오전 7시 실행되는 작업"""
    logger.info(f"\n{'#'*60}")
    logger.info(f"# 스케줄 작업 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"{'#'*60}")
    try:
        main.run(dry_run=False, privacy="public")
        logger.info("스케줄 작업 완료!")
    except Exception as e:
        logger.error(f"스케줄 작업 오류: {e}", exc_info=True)


if __name__ == "__main__":
    scheduler = BlockingScheduler(timezone="Asia/Seoul")

    # 매일 오전 7시 실행
    scheduler.add_job(
        daily_job,
        trigger=CronTrigger(hour=7, minute=0, timezone="Asia/Seoul"),
        id="daily_upload",
        name="비즈니스 일본어 YouTube 업로드",
        replace_existing=True,
    )

    logger.info("=" * 60)
    logger.info("비즈니스 일본어 YouTube 자동 업로드 스케줄러 시작")
    logger.info("실행 시간: 매일 오전 07:00 (KST)")
    logger.info("종료: Ctrl+C")
    logger.info("=" * 60)

    # 다음 실행 시간 출력
    job = scheduler.get_job("daily_upload")
    if job:
        logger.info(f"다음 실행: {job.next_run_time}")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("스케줄러 종료됨")
