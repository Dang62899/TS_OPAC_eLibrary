"""
Manual Item Status Update Script
Use this to manually change item statuses for testing or administrative purposes
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elibrary.settings')
django.setup()

from catalog.models import Item, Publication

# Example: Make all items of Publication 46 available
publication_id = 46  # Change this to the publication you want to update

pub = Publication.objects.get(id=publication_id)
items = Item.objects.filter(publication=pub)

print(f"Publication: {pub.title}")
print(f"\nCurrent Status:")
for item in items:
    barcode_display = item.barcode if getattr(item, 'barcode', None) else 'N/A'
    print(f"  ID {item.id} | Barcode: {barcode_display} | {item.status}")

# Update all items to 'available'
print(f"\nUpdating all items to 'available'...")
items.update(status='available')

print(f"\nNew Status:")
for item in Item.objects.filter(publication=pub):
    barcode_display = item.barcode if getattr(item, 'barcode', None) else 'N/A'
    print(f"  ID {item.id} | Barcode: {barcode_display} | {item.status}")

print("\nDone! Items are now available.")
print("Students can now create checkout requests for this publication.")
