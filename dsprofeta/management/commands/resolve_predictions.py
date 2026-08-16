from django.core.management.base import BaseCommand

from dsprofeta.services import resolve_predictions


class Command(BaseCommand):
    help = "Completa el precio real (actual_close) de predicciones cuya target_time ya pasó."

    def handle(self, *args, **options):
        resolved = resolve_predictions()
        self.stdout.write(self.style.SUCCESS(f"{resolved} predicciones resueltas."))
