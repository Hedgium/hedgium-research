from django.core.management.base import BaseCommand

from market_data.services.fii_dii import ingest_fii_dii


class Command(BaseCommand):
    help = "Ingest FII/DII provisional flows from NSE"

    def handle(self, *args, **options):
        result = ingest_fii_dii()
        self.stdout.write(self.style.SUCCESS(str(result)))
