from django.core.management.base import BaseCommand

from scanner.models import Ticker
from scanner.services import DEFAULT_TICKERS, save_scan_results


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
        # El universo por defecto es DEFAULT_TICKERS más cualquier
        # ticker agregado manualmente desde el sitio (ver
        # scanner/views.py:add_ticker) que siga activo. Un Ticker
        # marcado is_active=False en el admin se excluye (ej. si se
        # deslistó) — is_active es un "opt-out", no una lista blanca.
        excluded = set(Ticker.objects.filter(is_active=False).values_list("symbol", flat=True))
        default_active = [s for s in DEFAULT_TICKERS if s not in excluded]
        custom_active = list(
            Ticker.objects.filter(is_active=True)
            .exclude(symbol__in=DEFAULT_TICKERS)
            .values_list("symbol", flat=True)
        )
        symbols = options["tickers"] or (default_active + custom_active)

        self.stdout.write(f"Escaneando {len(symbols)} tickers: {', '.join(symbols)}")
        saved = save_scan_results(symbols)
        self.stdout.write(self.style.SUCCESS(f"Guardados {saved} resultados."))
