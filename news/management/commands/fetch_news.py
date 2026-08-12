from django.core.management.base import BaseCommand

from news.models import NewsItem
from news.services import fetch_news_for_tickers
from scanner.models import Ticker
from scanner.services import DEFAULT_TICKERS


class Command(BaseCommand):
    help = "Descarga noticias de Yahoo Finance para los tickers del scanner y las guarda."

    def add_arguments(self, parser):
        parser.add_argument(
            "--tickers",
            nargs="*",
            default=None,
            help="Símbolos a consultar (por defecto, el universo completo en DEFAULT_TICKERS).",
        )

    def handle(self, *args, **options):
        excluded = set(Ticker.objects.filter(is_active=False).values_list("symbol", flat=True))
        symbols = options["tickers"] or [s for s in DEFAULT_TICKERS if s not in excluded]

        self.stdout.write(f"Buscando noticias para {len(symbols)} tickers: {', '.join(symbols)}")
        items = fetch_news_for_tickers(symbols)

        saved = 0
        for item in items:
            news_item, _ = NewsItem.objects.update_or_create(
                url=item["url"],
                defaults={
                    "title": item["title"],
                    "summary": item["summary"],
                    "source": item["source"],
                    "published_at": item["published_at"],
                },
            )
            tickers = [Ticker.objects.get_or_create(symbol=s)[0] for s in item["tickers"]]
            news_item.tickers.set(tickers)
            saved += 1

        self.stdout.write(self.style.SUCCESS(f"Guardadas {saved} noticias."))
