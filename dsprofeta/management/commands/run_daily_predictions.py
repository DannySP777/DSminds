from django.core.management.base import BaseCommand

from dsprofeta.ml import predict_next
from dsprofeta.models import Asset, Prediction

TIMEFRAME = "1d"


class Command(BaseCommand):
    """
    Genera la predicción diaria (1d) por defecto para cada activo activo
    de DSprofeta — separada de run_hourly_cycle (que solo auto-genera en
    1h) porque una predicción diaria solo tiene sentido regenerarla una
    vez por día, cuando cierra la vela diaria anterior. Pensada para
    correr una vez al día vía el scheduler (ver scanner/tasks.py::
    run_dsprofeta_daily_jobs), después de sync_prices/train_predictors.

    Mismo criterio que run_hourly_cycle: si ya hay una predicción diaria
    sin resolver para ese activo, se omite (se espera a que la vela de
    hoy cierre y la resuelva resolve_predictions) en vez de generar una
    segunda predicción sobre el mismo dato.
    """

    help = "Genera la predicción diaria (1d) para todos los activos activos de DSprofeta, si no hay una pendiente."

    def handle(self, *args, **options):
        for asset in Asset.objects.filter(is_active=True):
            has_pending = Prediction.objects.filter(
                asset=asset, timeframe=TIMEFRAME, actual_close__isnull=True,
            ).exists()
            if has_pending:
                self.stdout.write(f"{asset.symbol}: ya hay una predicción diaria pendiente — se omite.")
                continue

            try:
                prediction = predict_next(asset, TIMEFRAME)
                self.stdout.write(self.style.SUCCESS(
                    f"{asset.symbol} -> predicción diaria {prediction.predicted_close} "
                    f"para {prediction.target_time:%Y-%m-%d} UTC"
                ))
            except ValueError as exc:
                self.stdout.write(self.style.WARNING(f"{asset.symbol}: {exc}"))
