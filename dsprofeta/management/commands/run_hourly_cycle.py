from django.core.management.base import BaseCommand

from dsprofeta.ml import predict_next
from dsprofeta.models import Asset, Prediction
from dsprofeta.services import resolve_predictions, sync_prices

TIMEFRAME = "1h"


class Command(BaseCommand):
    """
    Ciclo horario de DSprofeta: resuelve las predicciones de 1h que ya
    vencieron (les completa el precio real), sincroniza las velas más
    recientes, y genera una predicción nueva por cada activo activo.
    Pensado para correr una vez por hora vía el scheduler (ver
    scanner/tasks.py) — así se va acumulando historial real de
    predicción-vs-real con el que calcular la confianza (dsprofeta/confidence.py).

    Cuando el mercado está cerrado (noche, fin de semana) yfinance no trae
    velas nuevas, así que no tiene sentido generar una predicción nueva
    cada hora igual — se acumularían varias predicciones pendientes
    sobre el mismo dato viejo. La regla es simple: si ya hay una
    predicción sin resolver para ese activo/frecuencia, se espera a que
    se resuelva (lo cual solo pasa cuando llega una vela real nueva)
    antes de generar la siguiente. Así, con el mercado cerrado, el ciclo
    simplemente no hace nada para ese activo en vez de generar ruido.
    """

    help = "Sincroniza, resuelve y predice (frecuencia 1h) para todos los activos activos de DSprofeta."

    def handle(self, *args, **options):
        resolved = resolve_predictions()
        self.stdout.write(f"Predicciones resueltas: {resolved}")

        for asset in Asset.objects.filter(is_active=True):
            saved = sync_prices(asset, TIMEFRAME)
            self.stdout.write(f"{asset.symbol}: {saved} velas sincronizadas")

            has_pending = Prediction.objects.filter(
                asset=asset, timeframe=TIMEFRAME, actual_close__isnull=True,
            ).exists()
            if has_pending:
                self.stdout.write(
                    f"{asset.symbol}: ya hay una predicción pendiente sin resolver "
                    f"(mercado probablemente cerrado o sin vela nueva) — se omite este ciclo."
                )
                continue

            try:
                prediction = predict_next(asset, TIMEFRAME)
                self.stdout.write(self.style.SUCCESS(
                    f"{asset.symbol} -> predicción {prediction.predicted_close} "
                    f"para {prediction.target_time:%Y-%m-%d %H:%M} UTC"
                ))
            except ValueError as exc:
                self.stdout.write(self.style.WARNING(f"{asset.symbol}: {exc}"))
