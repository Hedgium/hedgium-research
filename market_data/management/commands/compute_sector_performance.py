from datetime import datetime

from django.core.management.base import BaseCommand

from market_data.services.sector_performance import compute_sector_performance


class Command(BaseCommand):
    help = "Compute equal-weighted sector returns from OHLCV"

    def add_arguments(self, parser):
        parser.add_argument("--date", help="As-of date YYYY-MM-DD (default: today)")

    def handle(self, *args, **options):
        as_of = None
        if options.get("date"):
            as_of = datetime.strptime(options["date"], "%Y-%m-%d").date()
        result = compute_sector_performance(as_of_date=as_of)
        self.stdout.write(self.style.SUCCESS(str(result)))
