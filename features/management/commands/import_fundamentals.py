import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand

from features.models import FundamentalMetric
from symbols.models import Symbol


def _dec(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        return Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None


class Command(BaseCommand):
    help = "Import fundamental metrics CSV (ticker,period_end,pe,pb,roe,roce,debt_equity,profit_growth_yoy,revenue_growth_yoy)"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", help="Path to fundamentals CSV")

    def handle(self, *args, **options):
        created = 0
        updated = 0
        skipped = 0

        with open(options["csv_path"], newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                ticker = (row.get("ticker") or row.get("Ticker") or "").strip()
                if not ticker:
                    skipped += 1
                    continue
                symbol = Symbol.objects.filter(ticker=ticker, exchange=Symbol.Exchange.NSE).first()
                if not symbol:
                    skipped += 1
                    continue
                period_raw = (row.get("period_end") or row.get("period") or "").strip()
                try:
                    period_end = datetime.strptime(period_raw, "%Y-%m-%d").date()
                except ValueError:
                    skipped += 1
                    continue

                defaults = {
                    "pe": _dec(row.get("pe")),
                    "pb": _dec(row.get("pb")),
                    "roe": _dec(row.get("roe")),
                    "roce": _dec(row.get("roce")),
                    "debt_equity": _dec(row.get("debt_equity")),
                    "profit_growth_yoy": _dec(row.get("profit_growth_yoy")),
                    "revenue_growth_yoy": _dec(row.get("revenue_growth_yoy")),
                    "source": (row.get("source") or "csv").strip(),
                }
                _, was_created = FundamentalMetric.objects.update_or_create(
                    symbol=symbol,
                    period_end=period_end,
                    defaults=defaults,
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Fundamentals import: {created} created, {updated} updated, {skipped} skipped"
            )
        )
