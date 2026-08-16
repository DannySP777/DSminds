from django.core.management.base import BaseCommand
from django.utils import timezone as dj_timezone

from dsprofeta.charts import invalidate_prediction_chart
from dsprofeta.features import build_backtest_samples
from dsprofeta.ml import predict_from_features
from dsprofeta.models import Asset, Prediction


class Command(BaseCommand):
    """
    Simula el ciclo predicción -> resolución usando velas históricas YA
    sincronizadas, útil cuando el mercado está cerrado y no hay datos
    nuevos que esperar (fin de semana, fuera de horario): por cada una de
    las últimas --points velas, predice el cierre siguiente con el modelo
    activo y la resuelve al toque contra el cierre real que ya tenemos
    guardado en PriceBar. No es una predicción real "en vivo" — es una
    forma de generar datos con qué validar la curva predicción-vs-real y
    el indicador de confianza sin esperar a que abra el mercado.
    """

    help = "Backtest: simula predicciones resueltas sobre las últimas N velas históricas ya sincronizadas."

    def add_arguments(self, parser):
        parser.add_argument("--asset", default=None)
        parser.add_argument("--timeframe", default="15m")
        parser.add_argument("--points", type=int, default=30)

    def handle(self, *args, **options):
        timeframe = options["timeframe"]
        points = options["points"]
        assets = Asset.objects.filter(is_active=True)
        if options["asset"]:
            assets = assets.filter(symbol=options["asset"])

        for asset in assets:
            samples = build_backtest_samples(asset, timeframe, n_points=points)
            if not samples:
                self.stdout.write(self.style.WARNING(f"{asset.symbol}: no hay suficiente historial para backtest."))
                continue

            created = 0
            for sample in samples:
                try:
                    predicted_return, version = predict_from_features(asset, timeframe, sample["features"])
                except ValueError as exc:
                    self.stdout.write(self.style.WARNING(f"{asset.symbol}: {exc}"))
                    break

                predicted_close = sample["base_close"] * (1 + predicted_return)
                Prediction.objects.update_or_create(
                    asset=asset, timeframe=timeframe,
                    target_time=sample["target_time"], model_version=version,
                    defaults={
                        "predicted_close": round(predicted_close, 5),
                        "actual_close": round(sample["actual_close"], 5),
                        "resolved_at": dj_timezone.now(),
                    },
                )
                created += 1

            invalidate_prediction_chart(asset, timeframe)
            self.stdout.write(self.style.SUCCESS(f"{asset.symbol} ({timeframe}): {created} predicciones de backtest creadas y resueltas."))
