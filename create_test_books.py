"""
Script to create sample books with different availability statuses for testing checkout requests
"""
import os
import django
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elibrary.settings')
django.setup()

from catalog.models import Publication, Item, Author, Subject, PublicationType, Location
from circulation.models import Loan
from django.contrib.auth import get_user_model

User = get_user_model()

def create_test_books():
    """Create test publications with various availability scenarios"""

    # Get or create required data
    author, _ = Author.objects.get_or_create(
        first_name="Test",
        last_name="Author",
        defaults={'bio': 'Author for testing purposes'}
    )

    subject, _ = Subject.objects.get_or_create(
        name="Testing"
    )

    pub_type, _ = PublicationType.objects.get_or_create(
        name="Book",
        defaults={'code': 'BK', 'description': 'Standard book format'}
    )

    location, _ = Location.objects.get_or_create(
        code="MAIN",
        defaults={'name': 'Main Library', 'description': 'Main library location'}
    )

    # Get a test borrower (create if needed)
    borrower, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'testuser@library.com',
            'first_name': 'Test',
            'last_name': 'User',
            'user_type': 'student'
        }
    )
    if created:
        borrower.set_password('test123')
        borrower.save()
        print(f"Created test user: testuser / test123")

    print("\n=== Creating Test Books ===\n")

    # Scenario 1: Available book (2 copies, both available)
    pub1, created = Publication.objects.get_or_create(
        isbn='TEST-001-AVAILABLE',
        defaults={
            'title': 'Available Book - Ready to Request',
            'publication_date': timezone.now().date(),
            'publication_type': pub_type,
            'abstract': 'This book has 2 copies available. Perfect for testing checkout requests.'
        }
    )
    if created:
        pub1.authors.add(author)
        pub1.subjects.add(subject)
        # Create 2 available items
        for i in range(1, 3):
            Item.objects.create(
                publication=pub1,
                barcode=f'AVAIL-{i:03d}',
                location=location,
                status='available'
            )
        print(f"✓ Created: {pub1.title} (2 available copies)")

    # Scenario 2: Partially available (2 copies, 1 on loan, 1 available)
    pub2, created = Publication.objects.get_or_create(
        isbn='TEST-002-PARTIAL',
        defaults={
            'title': 'Partially Available Book',
            'publication_date': timezone.now().date(),
            'publication_type': pub_type,
            'abstract': 'This book has 2 copies: 1 on loan, 1 available.'
        }
    )
    if created:
        pub2.authors.add(author)
        pub2.subjects.add(subject)
        # Available item
        Item.objects.create(
            publication=pub2,
            barcode='PARTIAL-001',
            location=location,
            status='available'
        )
        # On loan item
        item_on_loan = Item.objects.create(
            publication=pub2,
            barcode='PARTIAL-002',
            location=location,
            status='on_loan'
        )
        # Create a loan for the on-loan item
        Loan.objects.create(
            item=item_on_loan,
            borrower=borrower,
            checkout_date=timezone.now(),
            due_date=timezone.now() + timedelta(days=14),
            status='on_loan'
        )
        print(f"✓ Created: {pub2.title} (1 available, 1 on loan)")

    # Scenario 3: All copies on loan (3 copies, all checked out)
    pub3, created = Publication.objects.get_or_create(
        isbn='TEST-003-UNAVAILABLE',
        defaults={
            'title': 'Unavailable Book - All Copies On Loan',
            'publication_date': timezone.now().date(),
            'publication_type': pub_type,
            'abstract': 'This book has 3 copies but ALL are currently on loan. Test reservation/hold feature!'
        }
    )
    if created:
        pub3.authors.add(author)
        pub3.subjects.add(subject)
        # Create 3 items, all on loan
        for i in range(1, 4):
            item = Item.objects.create(
                publication=pub3,
                barcode=f'UNAVAIL-{i:03d}',
                location=location,
                status='on_loan'
            )
            Loan.objects.create(
                item=item,
                borrower=borrower,
                checkout_date=timezone.now() - timedelta(days=i),
                due_date=timezone.now() + timedelta(days=14-i),
                status='on_loan'
            )
        print(f"✓ Created: {pub3.title} (0 available, 3 on loan)")

    # Scenario 4: Popular book with multiple copies (5 copies: 1 available, 4 on loan)
    pub4, created = Publication.objects.get_or_create(
        isbn='TEST-004-POPULAR',
        defaults={
            'title': 'Popular Book - High Demand',
            'publication_date': timezone.now().date(),
            'publication_type': pub_type,
            'abstract': 'Very popular book with 5 copies: 1 available, 4 on loan. Great for testing checkout queue.'
        }
    )
    if created:
        pub4.authors.add(author)
        pub4.subjects.add(subject)
        # 1 available
        Item.objects.create(
            publication=pub4,
            barcode='POPULAR-001',
            location=location,
            status='available'
        )
        # 4 on loan
        for i in range(2, 6):
            item = Item.objects.create(
                publication=pub4,
                barcode=f'POPULAR-{i:03d}',
                location=location,
                status='on_loan'
            )
            Loan.objects.create(
                item=item,
                borrower=borrower,
                checkout_date=timezone.now() - timedelta(days=i-1),
                due_date=timezone.now() + timedelta(days=15-i),
                status='on_loan'
            )
        print(f"✓ Created: {pub4.title} (1 available, 4 on loan)")

    # Scenario 5: Single copy on loan
    pub5, created = Publication.objects.get_or_create(
        isbn='TEST-005-SINGLE',
        defaults={
            'title': 'Single Copy Book - Currently Unavailable',
            'publication_date': timezone.now().date(),
            'publication_type': pub_type,
            'abstract': 'Only 1 copy exists and it is currently on loan. Perfect for testing hold/reservation.'
        }
    )
    if created:
        pub5.authors.add(author)
        pub5.subjects.add(subject)
        item = Item.objects.create(
            publication=pub5,
            barcode='SINGLE-001',
            location=location,
            status='on_loan'
        )
        Loan.objects.create(
            item=item,
            borrower=borrower,
            checkout_date=timezone.now() - timedelta(days=3),
            due_date=timezone.now() + timedelta(days=11),
            status='on_loan'
        )
        print(f"✓ Created: {pub5.title} (0 available, 1 on loan)")

    print("\n=== Summary ===")
    print(f"Total test publications created: 5")
    print(f"Total test items created: {2 + 2 + 3 + 5 + 1} items")
    print(f"\nTest user: testuser / test123")
    print(f"\nYou can now test:")
    print("  - Checkout requests for available books (IDs: {}, {})".format(pub1.id, pub2.id))
    print("  - Holds/reservations for unavailable books (IDs: {}, {}, {})".format(pub3.id, pub4.id, pub5.id))
    print("\nAccess these books at: http://127.0.0.1:8000/catalog/")

if __name__ == '__main__':
    create_test_books()
