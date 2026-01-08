import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elibrary.settings')
import django
django.setup()

from catalog.models import (
    PublicationType, Publisher, Author, Publication, Item, Subject, Location
)
from datetime import datetime, timedelta
import random

print("\n" + "="*60)
print("POPULATING DATABASE WITH SAMPLE DATA")
print("="*60 + "\n")

# 1. Publication Types
print("Creating publication types...")
pub_types = [
    ("Manual", "MAN", "Training and operational manuals"),
    ("SOP", "SOP", "Standard Operating Procedures"),
    ("Capstone Project", "CAP", "Capstone projects and theses"),
    ("TTP", "TTP", "Tactics, Techniques, and Procedures"),
]
for name, code, desc in pub_types:
    PublicationType.objects.get_or_create(name=name, defaults={'code': code, 'description': desc})
print(f"✓ {len(pub_types)} publication types created")

# 2. Publishers
print("\nCreating publishers...")
publishers_data = [
    ("Penguin Books", "UK"),
    ("Hachette Book Group", "USA"),
    ("HarperCollins", "USA"),
    ("Simon & Schuster", "USA"),
    ("Oxford University Press", "UK"),
]
publishers = []
for name, country in publishers_data:
    pub, created = Publisher.objects.get_or_create(
        name=name,
        defaults={'address': f'{country}'}
    )
    publishers.append(pub)
print(f"✓ {len(publishers)} publishers created")

# 3. Authors
print("\nCreating authors...")
authors_data = [
    ("George", "Orwell", "British writer"),
    ("Jane", "Austen", "English novelist"),
    ("F. Scott", "Fitzgerald", "American author"),
    ("Harper", "Lee", "American writer"),
    ("Haruki", "Murakami", "Japanese novelist"),
    ("Agatha", "Christie", "British mystery writer"),
    ("Stephen", "King", "American horror author"),
    ("J.K.", "Rowling", "British fantasy author"),
]
authors = []
for first, last, bio in authors_data:
    author, created = Author.objects.get_or_create(
        first_name=first,
        last_name=last,
        defaults={'bio': bio}
    )
    authors.append(author)
print(f"✓ {len(authors)} authors created")

# 4. Subjects
print("\nCreating subjects...")
subjects_data = ["Fiction", "Mystery", "Science Fiction", "Biography", "History", "Technology"]
subjects = []
for name in subjects_data:
    subject, created = Subject.objects.get_or_create(name=name)
    subjects.append(subject)
print(f"✓ {len(subjects)} subjects created")

# 5. Locations
print("\nCreating library locations...")
locations_data = [
    ("Main Floor", "MAIN"),
    ("2nd Floor", "FLOOR2"),
    ("Reference Section", "REF"),
    ("Digital Library", "DIGITAL")
]
locations = []
for name, code in locations_data:
    location, created = Location.objects.get_or_create(name=name, defaults={'code': code})
    locations.append(location)
print(f"✓ {len(locations)} locations created")

# 6. Publications (Books)
print("\nCreating publications...")
publications_data = [
    ("1984", "George", "Orwell", 2013, "A dystopian social science fiction novel", 1949),
    ("Pride and Prejudice", "Jane", "Austen", 2003, "A romantic novel of manners", 1813),
    ("The Great Gatsby", "F. Scott", "Fitzgerald", 2004, "Jazz Age novel", 1925),
    ("To Kill a Mockingbird", "Harper", "Lee", 2006, "American classic", 1960),
    ("Norwegian Wood", "Haruki", "Murakami", 2010, "Japanese contemporary novel", 1987),
    ("Murder on the Orient Express", "Agatha", "Christie", 2012, "Detective mystery", 1934),
    ("The Shining", "Stephen", "King", 2012, "Horror novel", 1977),
    ("Harry Potter and the Philosophers Stone", "J.K.", "Rowling", 2005, "Fantasy adventure", 1997),
]

publications = []
for title, first, last, pub_year, abstract, orig_year in publications_data:
    author = Author.objects.get(first_name=first, last_name=last)
    publisher = random.choice(publishers)
    pub_type = PublicationType.objects.get(name="Manual")
    
    pub, created = Publication.objects.get_or_create(
        title=title,
        defaults={
            'publisher': publisher,
            'publication_type': pub_type,
            'publication_date': datetime(orig_year, 1, 1),
            'abstract': abstract,
            'language': 'English',
            'pages': random.randint(200, 500),
            'isbn': f'978{random.randint(1000000000, 9999999999)}',
        }
    )
    publications.append(pub)
    if created:
        pub.authors.add(author)  # Add author to ManyToMany field
        pub.subjects.set(random.sample(subjects, 2))
        pub.save()

print(f"✓ {len(publications)} publications created")

# 7. Items (Physical Copies)
print("\nCreating library items...")
item_count = 0
for pub in publications:
    # Create 2-3 copies of each book
    num_copies = random.randint(2, 3)
    for i in range(num_copies):
        item, created = Item.objects.get_or_create(
            barcode=f'BAR{pub.id}{i+1:03d}',
            defaults={
                'publication': pub,
                'location': random.choice(locations),
                'acquisition_date': datetime.now() - timedelta(days=random.randint(30, 365)),
                'status': 'available',
            }
        )
        if created:
            item_count += 1

print(f"✓ {item_count} items (physical copies) created")

# Print summary
print("\n" + "="*60)
print("SAMPLE DATA SUMMARY")
print("="*60)
print(f"✓ Publication Types: {PublicationType.objects.count()}")
print(f"✓ Publishers: {Publisher.objects.count()}")
print(f"✓ Authors: {Author.objects.count()}")
print(f"✓ Subjects: {Subject.objects.count()}")
print(f"✓ Locations: {Location.objects.count()}")
print(f"✓ Publications: {Publication.objects.count()}")
print(f"✓ Items: {Item.objects.count()}")
print("\n✓ Database populated successfully!")
print("="*60 + "\n")
