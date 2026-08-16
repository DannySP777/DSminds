"""
Programa el scan diario y la descarga de noticias con APScheduler.
Se arranca una sola vez desde scanner/apps.py cuando corre `runserver`.
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from django.core.management import call_command

logger = logging.getLogger(__name__)

_scheduler = None


def run_dsprofeta_hourly_cycle():
    try:
        call_command("run_hourly_cycle")
    except Exception:
        logger.exception("run_hourly_cycle (dsprofeta) falló")


def run_dsprofeta_daily_jobs():
    # Calendario económico y noticias: alimentan las features de RSI +
    # tasas de interés/PMI/empleo + noticias del modelo (dsprofeta/features.py).
    # No hacen nada si falta FINNHUB_API_KEY (ver dsprofeta/services.py),
    # así que es seguro dejarlos corriendo aunque todavía no esté configurada.
    try:
        call_command("sync_economic_calendar")
    except Exception:
        logger.exception("sync_economic_calendar (dsprofeta) falló")

    try:
        call_command("sync_market_news")
    except Exception:
        logger.exception("sync_market_news (dsprofeta) falló")

    # Reentrena todos los modelos activos con el historial acumulado hasta
    # hoy (incluye las predicciones ya resueltas del día) — así el modelo
    # va mejorando con el tiempo en vez de quedarse fijo con el primer
    # entrenamiento. Cada corrida queda registrada en ModelRun con su
    # propio MAE/RMSE (ver dsprofeta/confidence.py) para poder ver la
    # tendencia.
    try:
        call_command("train_predictors")
    except Exception:
        logger.exception("train_predictors (dsprofeta) falló")


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
    scheduler.add_job(
        run_dsprofeta_hourly_cycle,
        trigger=IntervalTrigger(hours=1),
        id="dsprofeta_hourly_cycle",
        replace_existing=True,
        misfire_grace_time=900,
    )
    scheduler.add_job(
        run_dsprofeta_daily_jobs,
        trigger=CronTrigger(hour=6, minute=0, timezone="UTC"),
        id="dsprofeta_daily_jobs",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info(
        "Scheduler iniciado: run_scan + fetch_news + fetch_calendar + generate_daily_summary "
        "(lun-vie 07:30 UTC), dsprofeta run_hourly_cycle (cada hora), "
        "dsprofeta sync_economic_calendar + sync_market_news + train_predictors (diario 06:00 UTC)."
    )
    return scheduler
