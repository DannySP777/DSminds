from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from news.models import EconomicEvent
from news.services import fetch_economic_calendar


class Command(BaseCommand):
    help = "Descarga el calendario económico semanal de EE.UU. (impacto medio/alto) y lo guarda."

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=7)
        deleted, _ = EconomicEvent.objects.filter(event_time__lt=cutoff).delete()
        if deleted:
            self.stdout.write(f"Eliminados {deleted} eventos vencidos.")

        events = fetch_economic_calendar()
        saved = 0
        for e in events:
            EconomicEvent.objects.update_or_create(
                title=e["title"],
                event_time=e["event_time"],
                defaults={
                    "country": e["country"],
                    "impact": e["impact"],
                    "forecast": e["forecast"],
                    "previous": e["previous"],
                    "actual": e["actual"],
                },
            )
            saved += 1

        self.stdout.write(self.style.SUCCESS(f"Guardados {saved} eventos del calendario económico."))
