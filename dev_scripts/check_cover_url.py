#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elibrary.settings')
django.setup()

from catalog.models import Publication

print("Checking cover image URLs...")
p = Publication.objects.filter(title='Digital Library').first()
if p:
    print(f"Title: {p.title}")
    print(f"Cover Image: {p.cover_image}")
    print(f"URL: {p.cover_image.url}")
    print(f"Full path: {p.cover_image.path}")
    print(f"\nFile exists: {os.path.exists(p.cover_image.path)}")
else:
    print("Book not found!")
