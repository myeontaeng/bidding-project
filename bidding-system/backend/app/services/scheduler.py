import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.crawlers.g2b_crawler import crawl_g2b
from app.services.announcement import (
    upsert_announcements, notify_new_announcements, send_dday_reminders,
    backfill_deadlines, close_expired_announcements,
)
from app.services.price_model import train_model
from app.services.result_tracker import poll_submitted_results

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def _run_crawl():
    logger.info("Crawl job start")
    try:
        items = await crawl_g2b(max_pages=3)
        async with AsyncSessionLocal() as db:
            new, dup = await upsert_announcements(db, items)
            logger.info("Crawl done: new=%d dup=%d", new, dup)
            await notify_new_announcements(db)
            closed = await close_expired_announcements(db)
            if closed:
                logger.info("Auto-closed %d expired announcements", closed)
    except Exception as e:
        logger.error("Crawl job failed: %s", e)


async def _run_reminders():
    logger.info("Reminder job start")
    try:
        async with AsyncSessionLocal() as db:
            await send_dday_reminders(db)
    except Exception as e:
        logger.error("Reminder job failed: %s", e)


async def _run_result_poll():
    logger.info("Result poll job start")
    try:
        async with AsyncSessionLocal() as db:
            await poll_submitted_results(db)
    except Exception as e:
        logger.error("Result poll failed: %s", e)


async def _run_model_retrain():
    logger.info("Model retrain job start")
    try:
        async with AsyncSessionLocal() as db:
            result = await train_model(db)
            logger.info("Model retrain done: %s", result)
    except Exception as e:
        logger.error("Model retrain failed: %s", e)


def start_scheduler():
    scheduler.add_job(
        _run_crawl,
        trigger=IntervalTrigger(minutes=settings.CRAWL_INTERVAL_MINUTES),
        id="crawl_g2b",
        replace_existing=True,
    )
    scheduler.add_job(
        _run_reminders,
        trigger=CronTrigger(hour=9, minute=0),
        id="dday_reminders",
        replace_existing=True,
    )
    scheduler.add_job(
        _run_result_poll,
        trigger=IntervalTrigger(hours=2),
        id="result_poll",
        replace_existing=True,
    )
    scheduler.add_job(
        _run_model_retrain,
        trigger=CronTrigger(day=1, hour=2, minute=0),
        id="model_retrain",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started (crawl every %dm, reminders 09:00, retrain monthly)", settings.CRAWL_INTERVAL_MINUTES)


def stop_scheduler():
    scheduler.shutdown(wait=False)
