"""Backfill normalized_isbn for existing Publication records.

This migration populates the `normalized_isbn` field for publications
added in migration 0002_add_normalized_isbn.py by removing hyphens
and spaces from the `isbn` field.
"""
from django.db import migrations
import re


def normalize_isbn(isbn):
    if not isbn:
        return ''
    # Remove hyphens and spaces and uppercase (keeps digits and X)
    return re.sub(r"[\s-]+", "", isbn).upper()


def forwards(apps, schema_editor):
    Publication = apps.get_model('catalog', 'Publication')
    for pub in Publication.objects.all():
        if pub.isbn:
            pub.normalized_isbn = normalize_isbn(pub.isbn)
            pub.save(update_fields=['normalized_isbn'])


def reverse(apps, schema_editor):
    # No-op reverse: we won't clear normalized_isbn on migration rollback
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0002_add_normalized_isbn'),
    ]

    operations = [
        migrations.RunPython(forwards, reverse),
    ]
