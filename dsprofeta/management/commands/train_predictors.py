from django.core.management.base import BaseCommand

from dsprofeta.ml import train
from dsprofeta.models import Asset, PriceBar


class Command(BaseCommand):
    help = "Entrena (o reentrena) el modelo LightGBM para uno o todos los pares activo+frecuencia."

    def add_arguments(self, parser):
        parser.add_argument("--asset", default=None)
        parser.add_argument("--timeframe", choices=[c[0] for c in PriceBar.Timeframe.choices], default=None)

    def handle(self, *args, **options):
        timeframes = [options["timeframe"]] if options["timeframe"] else [c[0] for c in PriceBar.Timeframe.choices]
        assets = Asset.objects.filter(is_active=True)
        if options["asset"]:
            assets = assets.filter(symbol=options["asset"])

        for asset in assets:
            for timeframe in timeframes:
                try:
                    run = train(asset, timeframe)
                except ValueError as exc:
                    self.stdout.write(self.style.WARNING(f"{asset.symbol} ({timeframe}): {exc}"))
                    continue
                self.stdout.write(self.style.SUCCESS(
                    f"{asset.symbol} ({timeframe}) v{run.version} — MAE={run.mae} RMSE={run.rmse} n={run.n_samples}"
                ))
