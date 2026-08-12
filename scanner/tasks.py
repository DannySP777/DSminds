"""
Programa el scan diario y la descarga de noticias con APScheduler.
Se arranca una sola vez desde scanner/apps.py cuando corre `runserver`.
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management import call_command

logger = logging.getLogger(__name__)

_scheduler = None


def run_daily_jobs():
    try:
        call_command("run_scan")
    except Exception:
        logger.exception("run_scan falló")

    try:
        call_command("fetch_news")
    except Exception:
        logger.exception("fetch_news falló")

    try:
        call_command("fetch_calendar")
    except Exception:
        logger.exception("fetch_calendar falló")

    try:
        call_command("generate_daily_summary")
    except Exception:
        logger.exception("generate_daily_summary falló")


def start_scheduler():
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        run_daily_jobs,
        trigger=CronTrigger(day_of_week="mon-fri", hour=7, minute=30, timezone="UTC"),
        id="daily_scan_and_news",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info(
        "Scheduler iniciado: run_scan + fetch_news + fetch_calendar + generate_daily_summary, "
        "lun-vie 07:30 UTC."
    )
    return scheduler
