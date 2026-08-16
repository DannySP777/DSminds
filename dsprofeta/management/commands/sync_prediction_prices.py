from django.core.management.base import BaseCommand

from dsprofeta.models import Asset, PriceBar
from dsprofeta.services import sync_prices


class Command(BaseCommand):
    help = "Sincroniza velas de precio (yfinance) para los activos activos de DSprofeta."

    def add_arguments(self, parser):
        parser.add_argument(
            "--timeframe", choices=[c[0] for c in PriceBar.Timeframe.choices], default=None,
            help="Si se omite, sincroniza las 5 frecuencias soportadas.",
        )
        parser.add_argument(
            "--asset", default=None,
            help="Symbol de un solo activo (ej. NDX100). Si se omite, todos los activos activos.",
        )

    def handle(self, *args, **options):
        timeframes = [options["timeframe"]] if options["timeframe"] else [c[0] for c in PriceBar.Timeframe.choices]
        assets = Asset.objects.filter(is_active=True)
        if options["asset"]:
            assets = assets.filter(symbol=options["asset"])

        for asset in assets:
            for timeframe in timeframes:
                saved = sync_prices(asset, timeframe)
                self.stdout.write(f"{asset.symbol} ({timeframe}): {saved} velas guardadas/actualizadas.")
