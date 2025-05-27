from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from config import SUPABASE_DB_URL
from services.interview import run_interview
from datetime import datetime, timezone
from apscheduler.jobstores.base import JobLookupError
import logging

import os

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(
    jobstores={
        'default': SQLAlchemyJobStore(url=os.environ["SUPABASE_DB_URL"])
    },
    timezone="UTC"
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

    except Exception as e:
        logger.exception(f"[Trigger Interview Error] Failed for {candidate_id}")


def schedule_interview(candidate_id: str, event: str, scheduled_time: datetime):
    job_id = f"{event}_{candidate_id}"
    scheduler.add_job(
        func=trigger_interview,
        trigger='date',
        run_date=scheduled_time,
        id=job_id,
        args=[candidate_id],
        replace_existing=True
    )
    logger.info(f"[Scheduler] Interview {event} scheduled for candidate {candidate_id} at {scheduled_time}")

def cancel_interview(candidate_id: str, event: str):
    job_id = f"{event}_{candidate_id}"
    try:
        scheduler.remove_job(job_id=job_id)
        logger.info(f"[Scheduler] Removed interview {event} for candidate {candidate_id} due to cancellation.")
    except JobLookupError:
        logger.warning(f"[Scheduler] No interview {event} found for candidate {candidate_id} — may have already been removed.")