from datetime import date

from django.core.management.base import BaseCommand

from scanner.fundamentals import get_fundamentals
from scanner.models import ScanResult, Ticker
from scanner.services import DEFAULT_TICKERS, run_daily_scan


class Command(BaseCommand):
    help = "Corre el scan diario sobre una lista de tickers y guarda los resultados."

    def add_arguments(self, parser):
        parser.add_argument(
            "--tickers",
            nargs="*",
            default=None,
            help="Lista de símbolos a escanear (por defecto, el universo completo en DEFAULT_TICKERS).",
        )

    def handle(self, *args, **options):
        # El universo por defecto es DEFAULT_TICKERS. Un Ticker marcado
        # is_active=False en el admin se excluye (ej. si se deslistó) —
        # is_active es un "opt-out", no una lista blanca.
        excluded = set(Ticker.objects.filter(is_active=False).values_list("symbol", flat=True))
        symbols = options["tickers"] or [s for s in DEFAULT_TICKERS if s not in excluded]

        self.stdout.write(f"Escaneando {len(symbols)} tickers: {', '.join(symbols)}")
        results = run_daily_scan(symbols)
        today = date.today()

        saved = 0
        for r in results:
            ticker, _ = Ticker.objects.get_or_create(symbol=r["symbol"])
            fundamentals = get_fundamentals(r["symbol"])
            ScanResult.objects.update_or_create(
                ticker=ticker,
                date=today,
                defaults={
                    "price": r["price"],
                    "rsi": r["rsi"],
                    "relative_volume": r["relative_volume"],
                    "breakout": r["breakout"],
                    "ma200": r["ma200"],
                    "above_ma200": r["above_ma200"],
                    "atr": r["atr"],
                    "stop_loss": r["stop_loss"],
                    "relative_strength": r["relative_strength"],
                    "target_price": fundamentals.get("target_mean_price"),
                    "market_cap": fundamentals.get("market_cap"),
                    "market_cap_display": fundamentals.get("market_cap_display") or "",
                    "trailing_pe": fundamentals.get("trailing_pe"),
                    "peg_ratio": fundamentals.get("peg_ratio"),
                    "debt_to_equity": fundamentals.get("debt_to_equity"),
                    "exchange": fundamentals.get("exchange") or "",
                    "score": r["score"],
                },
            )
            saved += 1

        self.stdout.write(self.style.SUCCESS(f"Guardados {saved} resultados para {today}."))
