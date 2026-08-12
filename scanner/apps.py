import os
import sys

from django.apps import AppConfig


class ScannerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "scanner"

    def ready(self):
        if "runserver" not in sys.argv:
            return
        if os.environ.get("RUN_MAIN") != "true":
            return

        from . import tasks

        tasks.start_scheduler()
