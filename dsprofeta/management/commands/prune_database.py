"""
Mantenimiento de la base de datos: borra lo que ya no hace falta y vigila que
el tamaño total no pase de un tope (por defecto 750 MB).

Por qué existe: el 2026-10-06 la base llenó su volumen de 500 MB y Postgres se
cayó, tumbando todo el sitio. El 90 % del espacio eran modelos de predicción
viejos (un modelo nuevo de ~0,5 MB por activo y frecuencia, cada día, sin
borrar los anteriores). Esta poda corre a diario (ver scanner/tasks.py) y
también se puede lanzar a mano:

    python manage.py prune_database              # poda normal + chequeo del tope
    python manage.py prune_database --dry-run    # solo muestra qué borraría
    python manage.py prune_database --max-mb 600 # otro tope

Dos niveles: (1) poda normal por antigüedad; (2) si aun así la base supera el
tope, poda agresiva (ventanas mucho más cortas) y VACUUM FULL para devolver el
espacio al disco. Lo que se conserva siempre: el modelo activo de cada
activo/frecuencia, los posts del blog, las páginas, los mensajes de contacto,
las velas diarias y semanales, y el último escaneo de cada acción.
"""
import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from django.utils import timezone

from dsprofeta.models import EconomicEvent as MarketEvent
from dsprofeta.models import ModelRun, NewsHeadline, Prediction, PriceBar
from news.models import EconomicEvent, NewsItem
from scanner.models import ScanResult

logger = logging.getLogger(__name__)

DEFAULT_MAX_MB = 750

# Ventanas de retención en días. Las noticias solo importan recientes (se
# muestran frescas y el modelo solo mira las últimas 6 horas): 1 semana.
NORMAL = {
    "bars_15m": 90, "bars_1h": 1095, "bars_4h": 1095,
    "news_items": 7, "headlines": 7, "market_events": 180, "calendar_events": 60,
    "scan_results": 365, "predictions": 180, "model_runs_keep": 3,
}
AGGRESSIVE = {
    "bars_15m": 30, "bars_1h": 365, "bars_4h": 365,
    "news_items": 3, "headlines": 3, "market_events": 60, "calendar_events": 45,
    "scan_results": 120, "predictions": 60, "model_runs_keep": 1,
}


def database_size_mb():
    """Tamaño actual de la base en MB (Postgres: pg_database_size; SQLite: páginas)."""
    with connection.cursor() as cursor:
        if connection.vendor == "postgresql":
            cursor.execute("SELECT pg_database_size(current_database())")
            return cursor.fetchone()[0] / 1024 / 1024
        cursor.execute("PRAGMA page_count")
        pages = cursor.fetchone()[0]
        cursor.execute("PRAGMA page_size")
        return pages * cursor.fetchone()[0] / 1024 / 1024


class Command(BaseCommand):
    help = "Poda datos antiguos y mantiene la base de datos por debajo de un tope de tamaño."

    def add_arguments(self, parser):
        parser.add_argument("--max-mb", type=int, default=DEFAULT_MAX_MB, help="Tope de tamaño de la base en MB (750 por defecto).")
        parser.add_argument("--dry-run", action="store_true", help="Solo cuenta lo que borraría, sin borrar.")

    # ------------------------------------------------------------------ helpers
    def _delete(self, label, queryset, dry_run):
        count = queryset.count()
        if count and not dry_run:
            queryset.delete()
        if count:
            self.stdout.write(f"  {label}: {count} filas {'(simulado)' if dry_run else 'borradas'}")
        return count

    def _prune_model_runs(self, keep, dry_run):
        total = 0
        for asset_id, timeframe in ModelRun.objects.order_by().values_list("asset_id", "timeframe").distinct():
            runs = ModelRun.objects.filter(asset_id=asset_id, timeframe=timeframe)
            kept = list(runs.order_by("-is_active", "-id").values_list("id", flat=True)[:keep])
            total += self._delete(f"modelos {asset_id}/{timeframe}", runs.exclude(id__in=kept), dry_run)
        return total

    def _prune(self, rules, dry_run):
        now = timezone.now()
        ago = lambda days: now - timedelta(days=days)  # noqa: E731
        total = 0
        total += self._prune_model_runs(rules["model_runs_keep"], dry_run)
        for tf, key in (("15m", "bars_15m"), ("1h", "bars_1h"), ("4h", "bars_4h")):
            total += self._delete(f"velas {tf}", PriceBar.objects.filter(timeframe=tf, timestamp__lt=ago(rules[key])), dry_run)
        total += self._delete("noticias", NewsItem.objects.filter(published_at__lt=ago(rules["news_items"])), dry_run)
        total += self._delete("titulares", NewsHeadline.objects.filter(published_at__lt=ago(rules["headlines"])), dry_run)
        total += self._delete("eventos de mercado", MarketEvent.objects.filter(event_time__lt=ago(rules["market_events"])), dry_run)
        total += self._delete("calendario", EconomicEvent.objects.filter(event_time__lt=ago(rules["calendar_events"])), dry_run)
        total += self._delete(
            "escaneos", ScanResult.objects.filter(date__lt=(now - timedelta(days=rules["scan_results"])).date()), dry_run,
        )
        # Solo predicciones ya resueltas: las pendientes siguen vigentes.
        total += self._delete(
            "predicciones", Prediction.objects.filter(actual_close__isnull=False, target_time__lt=ago(rules["predictions"])), dry_run,
        )
        return total

    def _vacuum(self, full):
        if connection.vendor != "postgresql":
            return
        tables = [m._meta.db_table for m in (ModelRun, PriceBar, NewsItem, NewsHeadline, MarketEvent, EconomicEvent, ScanResult, Prediction)]
        tables.append("django_session")
        # VACUUM no puede correr dentro de una transacción.
        connection.ensure_connection()
        previous = connection.connection.autocommit
        connection.connection.autocommit = True
        try:
            with connection.cursor() as cursor:
                for table in tables:
                    cursor.execute(f'VACUUM {"FULL " if full else ""}"{table}"')
        finally:
            connection.connection.autocommit = previous

    # ------------------------------------------------------------------- handle
    def handle(self, *args, **options):
        dry_run, max_mb = options["dry_run"], options["max_mb"]
        before = database_size_mb()
        self.stdout.write(f"Tamaño actual: {before:.1f} MB (tope {max_mb} MB)")

        self.stdout.write("Poda normal:")
        self._prune(NORMAL, dry_run)
        if not dry_run:
            call_command("clearsessions")
            self._vacuum(full=False)

        after = database_size_mb()
        if dry_run:
            self.stdout.write(self.style.SUCCESS("Simulación terminada: no se borró nada."))
            return

        if after > max_mb:
            self.stdout.write(self.style.WARNING(f"Sigue en {after:.1f} MB (> {max_mb}): poda agresiva."))
            logger.warning("prune_database: base en %.1f MB sobre el tope de %d MB; poda agresiva", after, max_mb)
            self._prune(AGGRESSIVE, dry_run=False)
            self._vacuum(full=True)
            after = database_size_mb()
            if after > max_mb:
                logger.error("prune_database: la base sigue en %.1f MB (tope %d MB) tras la poda agresiva", after, max_mb)
                self.stdout.write(self.style.ERROR(f"ATENCIÓN: sigue en {after:.1f} MB tras la poda agresiva. Revisar manualmente."))
                return

        self.stdout.write(self.style.SUCCESS(f"Listo: {before:.1f} MB -> {after:.1f} MB (tope {max_mb} MB)."))
