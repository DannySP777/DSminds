from django.core.management.base import BaseCommand

from dsprofeta.models import Asset

INITIAL_ASSETS = [
    {"symbol": "NDX100", "display_name": "NASDAQ 100", "yfinance_symbol": "^NDX", "asset_class": Asset.AssetClass.INDEX, "is_active": True},
    {"symbol": "GOLD", "display_name": "Oro", "yfinance_symbol": "GC=F", "asset_class": Asset.AssetClass.COMMODITY, "is_active": True},
    {"symbol": "EURUSD", "display_name": "EUR/USD", "yfinance_symbol": "EURUSD=X", "asset_class": Asset.AssetClass.FOREX, "is_active": True},
    {"symbol": "BTCUSD", "display_name": "BTC/USD", "yfinance_symbol": "BTC-USD", "asset_class": Asset.AssetClass.CRYPTO, "is_active": True},
    # SPX500 se mantiene en la base (no se borra, tiene historial de
    # PriceBar/Prediction) pero pasa a is_active=False — el rediseño de
    # "Trading con IA" (sep 2026) se enfoca en exactamente estos 4 activos
    # (NASDAQ, Oro, EUR/USD, BTC), pedido explícito del usuario.
    {"symbol": "SPX500", "display_name": "S&P 500", "yfinance_symbol": "^GSPC", "asset_class": Asset.AssetClass.INDEX, "is_active": False},
]


class Command(BaseCommand):
    help = "Crea/actualiza los activos de DSprofeta (NASDAQ 100, Oro, EUR/USD, BTC/USD; S&P 500 queda inactivo)."

    def handle(self, *args, **options):
        created = 0
        for data in INITIAL_ASSETS:
            symbol = data["symbol"]
            _, was_created = Asset.objects.update_or_create(symbol=symbol, defaults=data)
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f"Listo: {len(INITIAL_ASSETS)} activos verificados ({created} nuevos)."))
