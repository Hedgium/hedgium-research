from django.core.management.base import BaseCommand

from symbols.constants import NIFTY_50
from symbols.models import Company, IndexMembership, Sector, Symbol


class Command(BaseCommand):
    help = "Seed NIFTY 50 companies, symbols, and index memberships"

    def handle(self, *args, **options):
        created_sectors = 0
        created_companies = 0
        created_symbols = 0
        created_memberships = 0

        for row in NIFTY_50:
            sector, sector_created = Sector.objects.get_or_create(name=row["sector"])
            if sector_created:
                created_sectors += 1

            company, company_created = Company.objects.get_or_create(
                name=row["name"],
                defaults={"sector": sector},
            )
            if company_created:
                created_companies += 1
            elif company.sector_id != sector.id:
                company.sector = sector
                company.save(update_fields=["sector"])

            symbol, symbol_created = Symbol.objects.get_or_create(
                ticker=row["ticker"],
                exchange=Symbol.Exchange.NSE,
                defaults={"company": company, "is_active": True},
            )
            if symbol_created:
                created_symbols += 1

            _, membership_created = IndexMembership.objects.get_or_create(
                symbol=symbol,
                index_name="NIFTY50",
            )
            if membership_created:
                created_memberships += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"NIFTY 50 seed complete: "
                f"{created_sectors} sectors, {created_companies} companies, "
                f"{created_symbols} symbols, {created_memberships} memberships"
            )
        )
