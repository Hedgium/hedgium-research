from django.core.management.base import BaseCommand

from market_data.services.instruments import sync_nse_equity_tokens


class Command(BaseCommand):
    help = "Sync NSE instrument tokens from Kite instruments master"

    def add_arguments(self, parser):
        parser.add_argument(
            "--ticker",
            action="append",
            dest="tickers",
            help="Limit sync to specific ticker(s); repeatable",
        )

    def handle(self, *args, **options):
        result = sync_nse_equity_tokens(tickers=options.get("tickers"))
        self.stdout.write(self.style.SUCCESS(str(result)))
