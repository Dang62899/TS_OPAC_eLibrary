#!/usr/bin/env python
"""
System verification script - checks database integrity and application health
"""
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elibrary.settings')
django.setup()

from accounts.models import User
from catalog.models import Publication, PublicationType, Item, Location
from circulation.models import Loan, Hold
from django.conf import settings
from django.db import connection

def check_database_connection():
    """Test database connection"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True, "Connected"
    except Exception as e:
        return False, str(e)

def check_models():
    """Verify all models exist and have data"""
    checks = {
        "Users": User.objects.count(),
        "  - Admin": User.objects.filter(user_type='admin').count(),
        "  - Staff": User.objects.filter(user_type='staff').count(),
        "  - Borrowers": User.objects.filter(user_type='borrower').count(),
        "Publications": Publication.objects.count(),
        "Publication Types": PublicationType.objects.count(),
        "Items": Item.objects.count(),
        "  - Available": Item.objects.filter(status='available').count(),
        "  - On Loan": Item.objects.filter(status='on_loan').count(),
        "  - On Hold": Item.objects.filter(status='on_hold_shelf').count(),
        "Locations": Location.objects.count(),
        "Loans": Loan.objects.count(),
        "  - Active": Loan.objects.filter(status='active').count(),
        "  - Returned": Loan.objects.filter(status='returned').count(),
        "Holds": Hold.objects.count(),
    }
    return checks

def check_settings():
    """Verify critical settings"""
    settings_check = {
        "DEBUG": settings.DEBUG,
        "ALLOWED_HOSTS": settings.ALLOWED_HOSTS,
        "Database Engine": settings.DATABASES['default']['ENGINE'],
        "AUTH_USER_MODEL": settings.AUTH_USER_MODEL,
        "LOGIN_URL": settings.LOGIN_URL,
    }
    return settings_check

def main():
    print("\n" + "=" * 70)
    print("TS_OPAC eLIBRARY - SYSTEM VERIFICATION")
    print("=" * 70)
    
    # Database Connection
    print("\n🔌 DATABASE CONNECTION")
    print("-" * 70)
    connected, msg = check_database_connection()
    if connected:
        print("✅ Database connection: OK")
    else:
        print(f"❌ Database connection: FAILED - {msg}")
        sys.exit(1)
    
    # Django Settings
    print("\n⚙️  DJANGO SETTINGS")
    print("-" * 70)
    settings_check = check_settings()
    for key, value in settings_check.items():
        if isinstance(value, list):
            print(f"   {key}: {', '.join(value) if value else 'Not set'}")
        else:
            print(f"   {key}: {value}")
    
    # Data Integrity
    print("\n📊 DATA INTEGRITY")
    print("-" * 70)
    data_check = check_models()
    for key, count in data_check.items():
        if key.startswith("  -"):
            print(f"   {key}: {count}")
        else:
            print(f"✅ {key}: {count}")
    
    # Verification Results
    print("\n" + "=" * 70)
    
    # Check if critical data exists
    critical_pass = (
        User.objects.filter(user_type='admin').exists() and
        Publication.objects.exists() and
        Item.objects.exists() and
        Loan.objects.exists()
    )
    
    if critical_pass:
        print("✅ ALL SYSTEM CHECKS PASSED - APPLICATION IS READY")
    else:
        print("⚠️  WARNING - Missing critical data:")
        if not User.objects.filter(user_type='admin').exists():
            print("   - No admin user found")
        if not Publication.objects.exists():
            print("   - No publications in database")
        if not Item.objects.exists():
            print("   - No items in database")
        if not Loan.objects.exists():
            print("   - No loan records in database")
    
    print("=" * 70 + "\n")
    return 0 if critical_pass else 1

if __name__ == "__main__":
    sys.exit(main())
