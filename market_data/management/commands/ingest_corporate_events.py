from datetime import datetime, timedelta

from django.core.management.base import BaseCommand

from market_data.services.corporate_events import ingest_corporate_actions


class Command(BaseCommand):
    help = "Ingest corporate actions from NSE for index constituents"

    def add_arguments(self, parser):
        parser.add_argument("--from-date", help="From date YYYY-MM-DD")
        parser.add_argument("--to-date", help="To date YYYY-MM-DD")
        parser.add_argument("--days", type=int, default=30, help="Lookback if from-date omitted")
        parser.add_argument("--index", default="NIFTY50")

    def handle(self, *args, **options):
        to_date = None
        from_date = None
        if options.get("to_date"):
            to_date = datetime.strptime(options["to_date"], "%Y-%m-%d").date()
        if options.get("from_date"):
            from_date = datetime.strptime(options["from_date"], "%Y-%m-%d").date()
        elif to_date:
            from_date = to_date - timedelta(days=options["days"])
        else:
            from_date = None
            to_date = None

        result = ingest_corporate_actions(
            from_date=from_date,
            to_date=to_date,
            index_name=options["index"],
        )
        self.stdout.write(self.style.SUCCESS(str(result)))
