import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone as dj_timezone

from dsprofeta.ml import predict_next
from dsprofeta.models import Asset
from dsprofeta.services import resolve_predictions, sync_prices


class Command(BaseCommand):
    """
    Utilidad de prueba SOLO LOCAL: cada `--interval` minutos sincroniza
    precios, genera una predicción nueva por activo y resuelve las que ya
    vencieron. Sirve para validar el ciclo completo (predicción → real →
    curva) sin esperar un día real. No reemplaza al scheduler de
    producción (scanner/tasks.py) — eso es un paso aparte, ya en fase de
    despliegue.
    """

    help = "Corre el ciclo predicción/resolución en un loop local, pensado para validar rápido (default: 2h, cada 15min)."

    def add_arguments(self, parser):
        parser.add_argument("--minutes", type=int, default=120, help="Duración total en minutos (default 120).")
        parser.add_argument("--interval", type=int, default=15, help="Minutos entre cada ciclo (default 15).")
        parser.add_argument("--timeframe", default="15m")

    def handle(self, *args, **options):
        duration = options["minutes"]
        interval = options["interval"]
        timeframe = options["timeframe"]
        deadline = dj_timezone.now() + timedelta(minutes=duration)

        cycle = 0
        while dj_timezone.now() < deadline:
            cycle += 1
            self.stdout.write(f"--- Ciclo {cycle} - {dj_timezone.now():%H:%M:%S} UTC ---")

            resolved = resolve_predictions()
            self.stdout.write(f"Predicciones resueltas: {resolved}")

            for asset in Asset.objects.filter(is_active=True):
                saved = sync_prices(asset, timeframe)
                self.stdout.write(f"{asset.symbol}: {saved} velas sincronizadas")
                try:
                    prediction = predict_next(asset, timeframe)
                    self.stdout.write(
                        f"{asset.symbol} -> predicción {prediction.predicted_close} para {prediction.target_time:%H:%M} UTC"
                    )
                except ValueError as exc:
                    self.stdout.write(self.style.WARNING(f"{asset.symbol}: {exc}"))

            remaining = (deadline - dj_timezone.now()).total_seconds()
            if remaining <= 0:
                break
            time.sleep(min(interval * 60, remaining))

        self.stdout.write(self.style.SUCCESS(f"Loop de prueba local terminado ({cycle} ciclos)."))
