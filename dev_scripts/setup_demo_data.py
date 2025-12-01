#!/usr/bin/env python
"""
Management command to set up complete demo data for e-Library
Creates permanent admin and temporary demo accounts with sample data
"""
import os
import django
from datetime import timedelta
from django.utils import timezone
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elibrary.settings')
django.setup()

from accounts.models import User
from catalog.models import Publication, PublicationType, Author, Subject, Item, Location
from circulation.models import Loan

# Sample data - Technical and procedural documents
BOOK_DATA = [
    {"title": "Network Security Fundamentals Manual", "isbn": "978-1234567890", "author": "Security Team", "year": 2023},
    {"title": "Incident Response Procedures Guide", "isbn": "978-1234567891", "author": "IR Team", "year": 2023},
    {"title": "Cybersecurity Operations SOP", "isbn": "978-1234567892", "author": "Operations", "year": 2023},
    {"title": "Data Classification Standard", "isbn": "978-1234567893", "author": "Compliance", "year": 2022},
    {"title": "Vulnerability Management Process", "isbn": "978-1234567894", "author": "Vulnerability Team", "year": 2023},
    {"title": "Threat Intelligence Analysis TTP", "isbn": "978-1234567895", "author": "Intel Team", "year": 2023},
    {"title": "Access Control Implementation Manual", "isbn": "978-1234567896", "author": "IAM Team", "year": 2023},
    {"title": "Malware Analysis Procedures", "isbn": "978-1234567897", "author": "Malware Team", "year": 2022},
    {"title": "Network Architecture Design Guide", "isbn": "978-1234567898", "author": "Network Team", "year": 2023},
    {"title": "Forensics and Evidence Handling SOP", "isbn": "978-1234567899", "author": "Forensics Team", "year": 2023},
    {"title": "Penetration Testing Framework", "isbn": "978-1234567900", "author": "Pen Test Team", "year": 2023},
    {"title": "SIEM Administration Manual", "isbn": "978-1234567901", "author": "SIEM Team", "year": 2022},
    {"title": "Cloud Security Assessment Procedures", "isbn": "978-1234567902", "author": "Cloud Team", "year": 2023},
    {"title": "Intrusion Detection System Tuning Guide", "isbn": "978-1234567903", "author": "Detection Team", "year": 2023},
    {"title": "Compliance Audit Procedures", "isbn": "978-1234567904", "author": "Compliance Team", "year": 2022},
    {"title": "Security Awareness Training Materials", "isbn": "978-1234567905", "author": "Training Team", "year": 2023},
    {"title": "Capstone: Advanced Threat Detection System", "isbn": "978-1234567906", "author": "John Smith", "year": 2023},
    {"title": "Capstone: Zero Trust Architecture Implementation", "isbn": "978-1234567907", "author": "Jane Doe", "year": 2023},
    {"title": "Wireless Security Assessment TTP", "isbn": "978-1234567908", "author": "Wireless Team", "year": 2023},
    {"title": "Security Patch Management SOP", "isbn": "978-1234567909", "author": "Patch Team", "year": 2023},
]

def cleanup_database():
    """Delete all existing data"""
    print("\n🗑️  Cleaning up existing data...")
    # Delete in proper order due to foreign key constraints
    Loan.objects.all().delete()
    Item.objects.all().delete()
    Publication.objects.all().delete()
    User.objects.all().delete()
    print("✓ Database cleaned")

def create_locations():
    """Create library locations"""
    print("\n📍 Creating library locations...")
    locations = [
        Location.objects.get_or_create(
            name="Main Library",
            defaults={"code": "MAIN", "description": "Central library location"}
        )[0],
        Location.objects.get_or_create(
            name="East Branch",
            defaults={"code": "EAST", "description": "East side branch library"}
        )[0],
        Location.objects.get_or_create(
            name="West Branch",
            defaults={"code": "WEST", "description": "West side branch library"}
        )[0],
    ]
    print(f"✓ Created {len(locations)} locations")
    return locations

def create_publication_types():
    """Create publication types"""
    print("\n📚 Creating publication types...")
    types_data = [
        {"name": "Manual", "code": "MAN", "description": "Technical and user manuals"},
        {"name": "Standard Operating Procedure (SOP)", "code": "SOP", "description": "Standard operating procedures and guidelines"},
        {"name": "Capstone Project", "code": "CAP", "description": "Student capstone projects and theses"},
        {"name": "Tactics, Techniques, and Procedures (TTP)", "code": "TTP", "description": "Tactical and procedural documents"},
    ]
    types = []
    for t in types_data:
        obj, created = PublicationType.objects.get_or_create(
            name=t["name"],
            defaults={"code": t["code"], "description": t["description"]}
        )
        types.append(obj)
    print(f"✓ Created {len(types)} publication types")
    return types

def create_accounts():
    """Create user accounts"""
    print("\n👥 Creating user accounts...")
    
    # Permanent admin account
    admin, created = User.objects.get_or_create(
        username="admin",
        defaults={
            "email": "admin@elibrary.local",
            "first_name": "System",
            "last_name": "Administrator",
            "user_type": "admin",
            "is_staff": True,
            "is_superuser": True,
        }
    )
    if created:
        admin.set_password("admin123")
        admin.save()
        print("✓ PERMANENT Admin: admin / admin123")
    
    # Temporary demo staff account
    staff, created = User.objects.get_or_create(
        username="staff",
        defaults={
            "email": "staff@elibrary.local",
            "first_name": "Demo",
            "last_name": "Librarian",
            "user_type": "staff",
            "is_staff": True,
            "is_superuser": False,
        }
    )
    if created:
        staff.set_password("staff123")
        staff.save()
        print("✓ TEMPORARY Demo Staff: staff / staff123 (⚠️ For testing only)")
    
    # Temporary demo student account
    student, created = User.objects.get_or_create(
        username="student",
        defaults={
            "email": "student@elibrary.local",
            "first_name": "Demo",
            "last_name": "Borrower",
            "user_type": "borrower",
            "is_staff": False,
            "is_superuser": False,
            "library_card_number": "DEM001",
        }
    )
    if created:
        student.set_password("student123")
        student.save()
        print("✓ TEMPORARY Demo Student: student / student123 (⚠️ For testing only)")
    
    return admin, staff, student

def create_publications(pub_types):
    """Create sample publications"""
    print("\n📖 Creating sample publications...")
    publications = []
    
    for book in BOOK_DATA:
        from datetime import date
        pub, created = Publication.objects.get_or_create(
            isbn=book["isbn"],
            defaults={
                "title": book["title"],
                "publication_date": date(book["year"], 1, 1),
                "publication_type": random.choice(pub_types),
                "abstract": f"Technical document authored by {book['author']}. Published {book['year']}.",
            }
        )
        if created:
            publications.append(pub)
    
    print(f"✓ Created {len(publications)} sample publications")
    return publications

def create_items(publications, locations):
    """Create items with shuffled status"""
    print("\n📦 Creating sample items with shuffled status...")
    
    items = []
    item_statuses = [
        ("available", 0.70),      # 70% available
        ("on_hold_shelf", 0.15),  # 15% on hold
        ("on_loan", 0.15),        # 15% on loan
    ]
    
    for pub in publications:
        # Create 2-3 copies per publication
        num_copies = random.randint(2, 3)
        for i in range(num_copies):
            # Randomly select status based on distribution
            status = random.choices(
                [s[0] for s in item_statuses],
                [s[1] for s in item_statuses]
            )[0]
            
            item = Item.objects.create(
                publication=pub,
                location=random.choice(locations),
                barcode=f"BAR{pub.id:04d}{i:02d}",
                status=status,
                times_borrowed=random.randint(0, 10),
            )
            items.append(item)
    
    print(f"✓ Created {len(items)} items")
    status_counts = {
        "available": len([i for i in items if i.status == "available"]),
        "on_loan": len([i for i in items if i.status == "on_loan"]),
        "on_hold_shelf": len([i for i in items if i.status == "on_hold_shelf"]),
    }
    for status, count in status_counts.items():
        print(f"  - {status}: {count}")
    
    return items

def create_sample_loans(student, staff, items):
    """Create sample loans for student"""
    print("\n🔖 Creating sample loans for student account...")
    
    available_items = [i for i in items if i.status == "available" or i.status == "on_loan"]
    num_loans = random.randint(2, 4)
    
    loans = []
    for i in range(num_loans):
        if not available_items:
            break
        
        item = random.choice(available_items)
        available_items.remove(item)
        
        # Create loan with various due dates
        checkout_date = timezone.now() - timedelta(days=random.randint(0, 10))
        due_date = checkout_date + timedelta(days=14)
        
        loan = Loan.objects.create(
            item=item,
            borrower=student,
            checkout_staff=staff,
            checkout_date=checkout_date,
            due_date=due_date,
            status="active"
        )
        loans.append(loan)
        item.status = "on_loan"
        item.save()
    
    print(f"✓ Created {len(loans)} sample loans for student")
    return loans

def main():
    """Run complete setup"""
    print("\n" + "=" * 80)
    print("E-LIBRARY DEMO DATA SETUP")
    print("=" * 80)
    
    try:
        # Step 1: Cleanup
        cleanup_database()
        
        # Step 2: Create locations and types
        locations = create_locations()
        pub_types = create_publication_types()
        
        # Step 3: Create accounts
        admin, staff, student = create_accounts()
        
        # Step 4: Create publications
        publications = create_publications(pub_types)
        
        # Step 5: Create items with status
        items = create_items(publications, locations)
        
        # Step 6: Create sample loans
        loans = create_sample_loans(student, staff, items)
        
        # Summary
        print("\n" + "=" * 80)
        print("✅ SETUP COMPLETE - E-LIBRARY IS READY FOR TESTING")
        print("=" * 80)
        print("\n📋 LOGIN CREDENTIALS:")
        print("\n⭐ PERMANENT ACCOUNT (Production Use):")
        print("   Admin: admin / admin123")
        print("\n⚠️  TEMPORARY DEMO ACCOUNTS (Testing Only):")
        print("   Staff:   staff / staff123")
        print("   Student: student / student123")
        print("\n📊 DATA SUMMARY:")
        print(f"   - Publications: {Publication.objects.count()}")
        print(f"   - Items Total: {Item.objects.count()}")
        print(f"   - Available: {Item.objects.filter(status='available').count()}")
        print(f"   - On Loan: {Item.objects.filter(status='on_loan').count()}")
        print(f"   - On Hold: {Item.objects.filter(status='on_hold_shelf').count()}")
        print(f"   - Student Loans: {Loan.objects.filter(borrower=student).count()}")
        print("\n🌐 Access at: http://127.0.0.1:8000/")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
