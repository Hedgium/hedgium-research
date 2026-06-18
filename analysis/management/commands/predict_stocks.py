from django.core.management.base import BaseCommand

from analysis.ml.predict import predict_symbol, predict_universe
from symbols.models import Symbol


class Command(BaseCommand):
    help = "Run XGBoost predictions for NIFTY 50 or a single ticker"

    def add_arguments(self, parser):
        parser.add_argument("--index", default="NIFTY50")
        parser.add_argument("--ticker", help="Single ticker e.g. TCS")

    def handle(self, *args, **options):
        ticker = options.get("ticker")
        if ticker:
            symbol = Symbol.objects.get(ticker=ticker, exchange=Symbol.Exchange.NSE)
            result = predict_symbol(symbol)
        else:
            result = predict_universe(index_name=options["index"])

        style = self.style.SUCCESS if result.get("status") in ("success",) else self.style.WARNING
        self.stdout.write(style(str(result)))
