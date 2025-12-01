from django.core.management.base import BaseCommand
from catalog.models import Author, Publication, PublicationType
from datetime import date

class Command(BaseCommand):
    help = 'Populate database with sample books with cover images'

    def handle(self, *args, **options):
        # Create or get publication types
        fiction, _ = PublicationType.objects.get_or_create(
            name='Fiction',
            defaults={'description': 'Fiction books and novels', 'code': 'FIC'}
        )
        non_fiction, _ = PublicationType.objects.get_or_create(
            name='Non-Fiction',
            defaults={'description': 'Non-fiction and educational books', 'code': 'NF'}
        )

        # Sample books data
        books_data = [
            {
                'title': 'Digital Library',
                'subtitle': 'A Modern Guide',
                'author': 'John Smith',
                'publication_type': non_fiction,
                'isbn': '978-3-16-148410-0',
                'cover': 'books/sample_1.svg',
                'description': 'Comprehensive guide to modern digital library systems and management.',
                'pages': 350,
            },
            {
                'title': 'Knowledge Unveiled',
                'subtitle': 'Exploring Ideas & Innovation',
                'author': 'Sarah Johnson',
                'publication_type': non_fiction,
                'isbn': '978-0-06-112008-4',
                'cover': 'books/sample_2.svg',
                'description': 'Discover how knowledge shapes innovation in the modern world.',
                'pages': 280,
            },
            {
                'title': 'Nature & Science',
                'subtitle': 'Understanding Our World',
                'author': 'Dr. Michael Green',
                'publication_type': non_fiction,
                'isbn': '978-0-596-52068-7',
                'cover': 'books/sample_3.svg',
                'description': 'Explore the fascinating connections between nature and scientific discovery.',
                'pages': 420,
            },
            {
                'title': 'Fiction Worlds',
                'subtitle': 'Stories That Inspire',
                'author': 'Emma Watson',
                'publication_type': fiction,
                'isbn': '978-1-491-95246-4',
                'cover': 'books/sample_4.svg',
                'description': 'A collection of inspiring fictional tales from around the world.',
                'pages': 310,
            },
            {
                'title': 'History & Culture',
                'subtitle': 'Journey Through Time',
                'author': 'David Brown',
                'publication_type': non_fiction,
                'isbn': '978-1-449-32518-0',
                'cover': 'books/sample_5.svg',
                'description': 'Travel through centuries of human history and cultural evolution.',
                'pages': 500,
            },
            {
                'title': 'Business & Success',
                'subtitle': 'Strategies for Growth',
                'author': 'Lisa Anderson',
                'publication_type': non_fiction,
                'isbn': '978-0-13-468599-1',
                'cover': 'books/sample_6.svg',
                'description': 'Proven strategies and insights for business success and growth.',
                'pages': 290,
            },
        ]

        created_count = 0
        for book_data in books_data:
            author_name = book_data.pop('author')
            
            # Get or create author
            author, _ = Author.objects.get_or_create(
                name=author_name,
                defaults={'bio': f'Author of multiple publications'}
            )

            # Create publication if it doesn't exist
            pub, created = Publication.objects.get_or_create(
                isbn=book_data['isbn'],
                defaults={
                    **book_data,
                    'publication_date': date(2024, 1, 15),
                    'language': 'English',
                    'available_copies': 5,
                    'total_copies': 5,
                }
            )
            
            # Add author if not already added
            if created:
                pub.authors.add(author)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {pub.title}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'- Already exists: {pub.title}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully created {created_count} sample books!')
        )
