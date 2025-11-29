from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from catalog.models import PublicationType, Location, Subject, Author, Publisher, Publication, Item
from datetime import date

User = get_user_model()

class Command(BaseCommand):
    help = 'Create initial data for the e-library system'

    def handle(self, *args, **options):
        self.stdout.write('Creating initial data...')

        # Create Publication Types
        types_data = [
            ('Manuals', 'MAN', 'Technical and user manuals'),
            ('SOPs', 'SOP', 'Standard Operating Procedures'),
            ('Capstone Projects', 'CAP', 'Student capstone projects'),
            ('TTPs', 'TTP', 'Tactics, Techniques, and Procedures'),
        ]

        for name, code, desc in types_data:
            pub_type, created = PublicationType.objects.get_or_create(
                code=code,
                defaults={'name': name, 'description': desc}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created publication type: {name}'))

        # Create Locations
        locations_data = [
            ('Main Library', 'MAIN', 'Main library building', True),
            ('Digital Collection', 'DIGI', 'Digital/online resources', False),
            ('Reference Section', 'REF', 'Reference materials', True),
            ('Archives', 'ARCH', 'Archived materials', True),
        ]

        for name, code, desc, is_phys in locations_data:
            location, created = Location.objects.get_or_create(
                code=code,
                defaults={'name': name, 'description': desc, 'is_physical': is_phys}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created location: {name}'))

        # Create Subjects
        subjects = [
            'Information Technology',
            'Engineering',
            'Project Management',
            'Quality Assurance',
            'Safety Procedures',
            'Research Methods',
            'Technical Writing',
            'Software Development',
        ]

        for subject_name in subjects:
            subject, created = Subject.objects.get_or_create(name=subject_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created subject: {subject_name}'))

        # Create Sample Authors
        authors_data = [
            ('John', 'Doe'),
            ('Jane', 'Smith'),
            ('Robert', 'Johnson'),
            ('Emily', 'Williams'),
        ]

        for first, last in authors_data:
            author, created = Author.objects.get_or_create(
                first_name=first,
                last_name=last
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created author: {first} {last}'))

        # Create Sample Publisher
        publisher, created = Publisher.objects.get_or_create(
            name='Technical Publications Inc.',
            defaults={
                'address': '123 Library Street, Book City, BC 12345',
                'website': 'https://example.com'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created publisher: {publisher.name}'))

        # Create Sample Staff User
        if not User.objects.filter(username='staff').exists():
            User.objects.create_user(
                username='staff',
                email='staff@elibrary.com',
                password='staff123',
                first_name='Library',
                last_name='Staff',
                user_type='staff'
            )
            self.stdout.write(self.style.SUCCESS('Created staff user (username: staff, password: staff123)'))

        # Create Sample Borrower
        if not User.objects.filter(username='borrower').exists():
            User.objects.create_user(
                username='borrower',
                email='borrower@elibrary.com',
                password='borrower123',
                first_name='John',
                last_name='Reader',
                user_type='borrower',
                library_card_number='LIB001'
            )
            self.stdout.write(self.style.SUCCESS('Created borrower user (username: borrower, password: borrower123)'))

        # Create Sample Publications
        manual_type = PublicationType.objects.get(code='MAN')
        sop_type = PublicationType.objects.get(code='SOP')
        main_location = Location.objects.get(code='MAIN')
        it_subject = Subject.objects.get(name='Information Technology')

        # Sample Manual
        if not Publication.objects.filter(title='System Administration Manual').exists():
            pub = Publication.objects.create(
                title='System Administration Manual',
                subtitle='Complete Guide to Server Management',
                publication_type=manual_type,
                publisher=publisher,
                publication_date=date(2024, 1, 15),
                edition='3rd Edition',
                isbn='978-1234567890',
                language='English',
                pages=450,
                abstract='Comprehensive guide for system administrators covering server setup, maintenance, and troubleshooting.',
                call_number='MAN-001-2024'
            )
            pub.authors.add(Author.objects.get(first_name='John', last_name='Doe'))
            pub.subjects.add(it_subject)

            # Create items for this publication
            for i in range(1, 4):
                Item.objects.create(
                    publication=pub,
                    barcode=f'MAN001-{i:03d}',
                    location=main_location,
                    status='available'
                )

            self.stdout.write(self.style.SUCCESS(f'Created publication: {pub.title} with 3 copies'))

        # Sample SOP
        if not Publication.objects.filter(title='Emergency Response Procedures').exists():
            pub = Publication.objects.create(
                title='Emergency Response Procedures',
                publication_type=sop_type,
                publisher=publisher,
                publication_date=date(2024, 3, 1),
                edition='2nd Edition',
                language='English',
                pages=120,
                abstract='Standard operating procedures for handling emergency situations.',
                call_number='SOP-005-2024'
            )
            pub.authors.add(Author.objects.get(first_name='Jane', last_name='Smith'))
            pub.subjects.add(Subject.objects.get(name='Safety Procedures'))

            # Create items
            for i in range(1, 3):
                Item.objects.create(
                    publication=pub,
                    barcode=f'SOP005-{i:03d}',
                    location=main_location,
                    status='available'
                )

            self.stdout.write(self.style.SUCCESS(f'Created publication: {pub.title} with 2 copies'))

        self.stdout.write(self.style.SUCCESS('Initial data creation completed!'))
        self.stdout.write('')
        self.stdout.write('You can now:')
        self.stdout.write('1. Login to admin with your superuser account')
        self.stdout.write('2. Login as staff (username: staff, password: staff123)')
        self.stdout.write('3. Login as borrower (username: borrower, password: borrower123)')
