#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elibrary.settings')
django.setup()

from catalog.models import Publication

print("Checking sample books...")
pubs = Publication.objects.order_by('-date_added')[:6]
print(f"Total publications found: {Publication.objects.count()}")
print("\nRecent 6 publications:")
for p in pubs:
    print(f"  Title: {p.title}")
    print(f"  Cover: {p.cover_image.name if p.cover_image else 'NONE'}")
    print(f"  ISBN: {p.isbn}")
    print()
