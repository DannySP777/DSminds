from django.core.management.base import BaseCommand

from dsprofeta.ml import predict_next
from dsprofeta.models import Asset, Prediction
from dsprofeta.services import resolve_predictions, sync_prices

# Solo se auto-genera una predicción nueva en esta frecuencia (ver abajo por
# qué). Pero las velas (PriceBar) de TODAS las frecuencias se sincronizan acá
# — si no, un usuario que mira el gráfico en 15m/4h/diaria/semanal ve datos
# congelados en la fecha del último sync manual, aunque el sitio siga "vivo".
TIMEFRAMES_TO_SYNC = ["15m", "1h", "4h", "1d", "1w"]
PREDICT_TIMEFRAME = "1h"


class Command(BaseCommand):
    """
    Ciclo horario de DSprofeta: resuelve las predicciones vencidas de
    cualquier frecuencia (les completa el precio real), sincroniza las
    velas más recientes de las 5 frecuencias, y genera una predicción
    nueva de 1h por cada activo activo. Pensado para correr una vez por
    hora vía el scheduler (ver scanner/tasks.py) — así se va acumulando
    historial real de predicción-vs-real con el que calcular la
    confianza (dsprofeta/confidence.py).

    Solo se auto-genera predicción en 1h (no en 15m/4h/diaria/semanal):
    el usuario puede generar esas manualmente desde el botón cuando
    quiera, y así no se acumulan predicciones pendientes sin uso en
    frecuencias que nadie está mirando.

    Cuando el mercado está cerrado (noche, fin de semana) yfinance no trae
    velas nuevas, así que no tiene sentido generar una predicción nueva
    cada hora igual — se acumularían varias predicciones pendientes
    sobre el mismo dato viejo. La regla es simple: si ya hay una
    predicción sin resolver para ese activo/frecuencia, se espera a que
    se resuelva (lo cual solo pasa cuando llega una vela real nueva)
    antes de generar la siguiente. Así, con el mercado cerrado, el ciclo
    simplemente no hace nada para ese activo en vez de generar ruido.
    """

    help = "Sincroniza las 5 frecuencias, resuelve predicciones vencidas y predice (1h) para todos los activos activos de DSprofeta."

    def handle(self, *args, **options):
        resolved = resolve_predictions()
        self.stdout.write(f"Predicciones resueltas: {resolved}")

        for asset in Asset.objects.filter(is_active=True):
            for timeframe in TIMEFRAMES_TO_SYNC:
                saved = sync_prices(asset, timeframe)
                self.stdout.write(f"{asset.symbol} ({timeframe}): {saved} velas sincronizadas")

            has_pending = Prediction.objects.filter(
                asset=asset, timeframe=PREDICT_TIMEFRAME, actual_close__isnull=True,
            ).exists()
            if has_pending:
                self.stdout.write(
                    f"{asset.symbol}: ya hay una predicción pendiente sin resolver "
                    f"(mercado probablemente cerrado o sin vela nueva) — se omite este ciclo."
                )
                continue

            try:
                prediction = predict_next(asset, PREDICT_TIMEFRAME)
                self.stdout.write(self.style.SUCCESS(
                    f"{asset.symbol} -> predicción {prediction.predicted_close} "
                    f"para {prediction.target_time:%Y-%m-%d %H:%M} UTC"
                ))
            except ValueError as exc:
                self.stdout.write(self.style.WARNING(f"{asset.symbol}: {exc}"))
