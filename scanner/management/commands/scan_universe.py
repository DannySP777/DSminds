from django.core.management.base import BaseCommand

from scanner.services import save_universe_results


class Command(BaseCommand):
    help = (
        "Descubre, clasifica (penny/monster/standard) y rankea el universo "
        "ampliado para la vista 'sistema solar' del scanner."
    )

    def add_arguments(self, parser):
        parser.add_argument("--lang", default="es")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Corre discover/bucket/rank pero no guarda nada en la base — imprime conteos y una muestra por grupo.",
        )

    def handle(self, *args, **options):
        if options["dry_run"]:
            from scanner.universe import build_universe

            ranked = build_universe(options["lang"])
            for group, entries in ranked.items():
                self.stdout.write(f"{group}: {len(entries)} candidatos")
                for e in entries[:5]:
                    self.stdout.write(
                        f"  #{e.get('_rank')} {e['_symbol']}: composite={e.get('_composite')} "
                        f"upside={e.get('_upside_pct')}% relvol={e.get('_relative_volume')}x "
                        f"price={e.get('_price')} mcap={e.get('_market_cap')}"
                    )
            return

        saved = save_universe_results(options["lang"])
        self.stdout.write(self.style.SUCCESS(f"Universo guardado: {saved} resultados."))
