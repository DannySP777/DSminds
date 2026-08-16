from django.core.management.base import BaseCommand

from dsprofeta.services import sync_economic_calendar


class Command(BaseCommand):
    help = "Sincroniza el calendario económico desde Finnhub."

    def handle(self, *args, **options):
        saved = sync_economic_calendar()
        self.stdout.write(self.style.SUCCESS(f"{saved} eventos económicos guardados/actualizados."))
