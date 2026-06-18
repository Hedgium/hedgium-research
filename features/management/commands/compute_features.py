from datetime import datetime

from django.core.management.base import BaseCommand

from features.services.compute import compute_features_for_symbol, compute_features_universe
from symbols.models import Symbol


class Command(BaseCommand):
    help = "Compute and persist feature snapshots (technical, volatility, fundamental, corporate risk)"

    def add_arguments(self, parser):
        parser.add_argument("--index", default="NIFTY50")
        parser.add_argument("--ticker", action="append", dest="tickers")
        parser.add_argument("--date", help="As-of date YYYY-MM-DD (default: today)")

    def handle(self, *args, **options):
        as_of = None
        if options.get("date"):
            as_of = datetime.strptime(options["date"], "%Y-%m-%d").date()

        tickers = options.get("tickers")
        if tickers and len(tickers) == 1:
            symbol = Symbol.objects.get(ticker=tickers[0], exchange=Symbol.Exchange.NSE)
            result = compute_features_for_symbol(symbol, as_of_date=as_of)
        else:
            result = compute_features_universe(
                index_name=options["index"],
                as_of_date=as_of,
                tickers=tickers,
            )

        style = self.style.SUCCESS if result.get("status") in ("success",) else self.style.WARNING
        self.stdout.write(style(str(result)))
