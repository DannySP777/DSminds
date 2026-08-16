from django.core.management.base import BaseCommand

from dsprofeta.services import sync_market_news


class Command(BaseCommand):
    help = "Sincroniza noticias generales de mercado desde Finnhub."

    def handle(self, *args, **options):
        saved = sync_market_news()
        self.stdout.write(self.style.SUCCESS(f"{saved} titulares guardados/actualizados."))
