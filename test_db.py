import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elibrary.settings')
import django
django.setup()

from catalog.models import Publication, Item, Author, PublicationType
from accounts.models import User
from circulation.models import Loan

print("\n" + "="*50)
print("DATABASE CONTENT SUMMARY")
print("="*50 + "\n")

# Publications
pub_count = Publication.objects.count()
print(f"📚 Publications: {pub_count}")
if pub_count > 0:
    for pub in Publication.objects.all()[:3]:
        print(f"   - {pub.title} ({pub.publication_date.year if pub.publication_date else 'N/A'})")

# Items
item_count = Item.objects.count()
print(f"\n📖 Items (Physical Copies): {item_count}")

# Users
user_count = User.objects.count()
admin_count = User.objects.filter(is_superuser=True).count()
print(f"\n👥 Users: {user_count} (Admin: {admin_count})")
for user in User.objects.filter(is_superuser=True):
    print(f"   - {user.username} (Admin)")

# Authors
author_count = Author.objects.count()
print(f"\n✍️  Authors: {author_count}")

# Publication Types
pub_type_count = PublicationType.objects.count()
print(f"\n📋 Publication Types: {pub_type_count}")
for pt in PublicationType.objects.all()[:5]:
    print(f"   - {pt.name}")

# Loans
loan_count = Loan.objects.count()
print(f"\n🔄 Active Loans: {loan_count}")

print("\n" + "="*50)
print("✓ Database connection verified successfully!")
print("="*50 + "\n")
