from django.core.management.base import BaseCommand

from market_data.services.ingestion import run_daily_ingestion


class Command(BaseCommand):
    help = "Run full post-market ingestion pipeline (OHLCV, bhavcopy, FII/DII, sectors, corp actions)"

    def add_arguments(self, parser):
        parser.add_argument("--ohlcv-days", type=int, default=5)

    def handle(self, *args, **options):
        result = run_daily_ingestion(ohlcv_days=options["ohlcv_days"])
        style = self.style.SUCCESS if result["status"] == "success" else self.style.WARNING
        self.stdout.write(style(str(result)))
