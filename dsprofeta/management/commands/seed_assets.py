from django.core.management.base import BaseCommand

from dsprofeta.models import Asset

INITIAL_ASSETS = [
    {"symbol": "NDX100", "display_name": "NASDAQ 100", "yfinance_symbol": "^NDX", "asset_class": Asset.AssetClass.INDEX},
    {"symbol": "GOLD", "display_name": "Oro", "yfinance_symbol": "GC=F", "asset_class": Asset.AssetClass.COMMODITY},
    {"symbol": "EURUSD", "display_name": "EUR/USD", "yfinance_symbol": "EURUSD=X", "asset_class": Asset.AssetClass.FOREX},
    {"symbol": "SPX500", "display_name": "S&P 500", "yfinance_symbol": "^GSPC", "asset_class": Asset.AssetClass.INDEX},
]


class Command(BaseCommand):
    help = "Crea los activos iniciales de DSprofeta (NASDAQ 100, Oro, EUR/USD, S&P 500)."

    def handle(self, *args, **options):
        created = 0
        for data in INITIAL_ASSETS:
            symbol = data["symbol"]
            _, was_created = Asset.objects.update_or_create(symbol=symbol, defaults=data)
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f"Listo: {len(INITIAL_ASSETS)} activos verificados ({created} nuevos)."))
