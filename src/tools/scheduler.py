import logging
from datetime import datetime

from apscheduler.jobstores.base import JobLookupError
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from config import APSCHEDULER_DB_NAME, SUPABASE_DB_URL
from services.interview import run_interview

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(
    jobstores={
        "default": SQLAlchemyJobStore(
            url=SUPABASE_DB_URL,
            tablename=APSCHEDULER_DB_NAME,
            engine_options={
                "pool_pre_ping": True
            },  # important for Supabase session pooler
        )
    },
    job_defaults={
        "misfire_grace_time": 300,  # Allow up to 5 minutes delay
        "coalesce": False  # Run all missed jobs separately if multiple were missed
    },
    timezone="UTC",
)


def start_scheduler():
    if not scheduler.running:
        scheduler.start()


import asyncio


def trigger_interview(candidate_id: str):
    try:
        coro = run_interview(candidate_id)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            asyncio.create_task(coro)
        else:
            asyncio.run(coro)

    except Exception:
        logger.exception(f"[Trigger Interview Error] Failed for {candidate_id}")


def schedule_interview(candidate_id: str, event: str, scheduled_time: datetime):
    job_id = f"{event}_{candidate_id}"
    scheduler.add_job(
        func=trigger_interview,
        trigger="date",
        run_date=scheduled_time,
        id=job_id,
        args=[candidate_id],
        replace_existing=True,
    )
    logger.info(
        f"[Scheduler] Interview {event} scheduled for candidate {candidate_id} at {scheduled_time}"
    )


def cancel_interview(candidate_id: str, event: str):
    job_id = f"{event}_{candidate_id}"
    try:
        scheduler.remove_job(job_id=job_id)
        logger.info(
            f"[Scheduler] Removed interview {event} for candidate {candidate_id} due to cancellation."
        )
    except JobLookupError:
        logger.warning(
            f"[Scheduler] No interview {event} found for candidate {candidate_id} — may have already been removed."
        )
