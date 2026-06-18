from datetime import datetime

from django.core.management.base import BaseCommand

from market_data.services.bhavcopy import ingest_bhavcopy


class Command(BaseCommand):
    help = "Ingest NSE bhavcopy (OHLCV + delivery %) for a trade date"

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            help="Trade date YYYY-MM-DD (default: today IST)",
        )
        parser.add_argument("--ticker", action="append", dest="tickers")

    def handle(self, *args, **options):
        trade_date = None
        if options.get("date"):
            trade_date = datetime.strptime(options["date"], "%Y-%m-%d").date()
        result = ingest_bhavcopy(trade_date=trade_date, tickers=options.get("tickers"))
        self.stdout.write(self.style.SUCCESS(str(result)))
