from django.core.management.base import BaseCommand

from market_data.services.ohlcv import ingest_ohlcv_universe


class Command(BaseCommand):
    help = "Ingest OHLCV from Kite historical API for NIFTY 50 (or subset)"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=5, help="Lookback days (incremental)")
        parser.add_argument(
            "--backfill-years",
            type=int,
            default=None,
            help="Backfill years of history (overrides --days)",
        )
        parser.add_argument("--index", default="NIFTY50")
        parser.add_argument("--ticker", action="append", dest="tickers")
        parser.add_argument(
            "--no-sync-tokens",
            action="store_true",
            help="Skip instrument token sync before ingest",
        )

    def handle(self, *args, **options):
        result = ingest_ohlcv_universe(
            index_name=options["index"],
            days=options["days"],
            backfill_years=options["backfill_years"],
            tickers=options.get("tickers"),
            sync_tokens=not options["no_sync_tokens"],
        )
        self.stdout.write(self.style.SUCCESS(str(result)))
