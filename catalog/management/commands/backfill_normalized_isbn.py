from django.core.management.base import BaseCommand
import re

from catalog.models import Publication


def normalize_isbn(isbn):
    if not isbn:
        return ""
    return re.sub(r"[\s-]+", "", isbn).upper()


class Command(BaseCommand):
    help = "Backfill Publication.normalized_isbn from existing isbn values."

    def handle(self, *args, **options):
        qs = Publication.objects.all()
        total = qs.count()
        updated = 0
        for pub in qs:
            if pub.isbn:
                new = normalize_isbn(pub.isbn)
                if pub.normalized_isbn != new:
                    pub.normalized_isbn = new
                    pub.save(update_fields=["normalized_isbn"])
                    updated += 1
        self.stdout.write(self.style.SUCCESS(f"Processed {total} publications, updated {updated}"))
