from datetime import datetime

from django.core.management.base import BaseCommand

from market_data.services.fii_dii import ingest_fii_dii


class Command(BaseCommand):
    help = "Ingest FII/DII provisional flows from NSE"

    def add_arguments(self, parser):
        parser.add_argument("--date", help="Trade date YYYY-MM-DD (default: today)")

    def handle(self, *args, **options):
        trade_date = None
        if options.get("date"):
            trade_date = datetime.strptime(options["date"], "%Y-%m-%d").date()
        result = ingest_fii_dii(trade_date=trade_date)
        self.stdout.write(self.style.SUCCESS(str(result)))
