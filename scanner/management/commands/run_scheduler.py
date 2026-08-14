"""
Corre el scheduler de tareas diarias como proceso independiente.

scanner/apps.py arranca el scheduler automáticamente solo bajo
`manage.py runserver` (conveniente en desarrollo, un solo proceso).
En producción el proceso web corre con gunicorn y puede tener más de
un worker — si cada worker arrancara su propio scheduler, el scan
diario se dispararía varias veces. Por eso en producción el scheduler
va en su propio proceso ("worker" / "background worker" en el panel
del hosting), corriendo este comando.
"""
import time

from django.core.management.base import BaseCommand

from scanner.tasks import start_scheduler


class Command(BaseCommand):
    help = "Arranca el scheduler de tareas diarias y lo mantiene corriendo en primer plano."

    def handle(self, *args, **options):
        start_scheduler()
        self.stdout.write(self.style.SUCCESS("Scheduler corriendo. Ctrl+C para detener."))
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            self.stdout.write("Scheduler detenido.")
