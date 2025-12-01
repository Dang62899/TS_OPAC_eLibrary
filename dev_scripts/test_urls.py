#!/usr/bin/env python
"""
URL routing verification - test that all major routes are accessible
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elibrary.settings')
django.setup()

from django.test import Client
from django.urls import reverse

def test_urls():
    """Test critical URLs"""
    client = Client()
    
    # URLs to test
    test_urls = [
        ('catalog:index', 'Home page'),
        ('accounts:login', 'Login page'),
        ('catalog:search', 'Search page'),
    ]
    
    # Staff/Admin URLs
    staff_urls = [
        ('circulation:staff_dashboard', 'Staff Dashboard'),
        ('circulation:checkout', 'Checkout'),
        ('circulation:checkin', 'Check-in'),
    ]
    
    print("\n" + "=" * 70)
    print("URL ROUTING TEST")
    print("=" * 70)
    
    print("\n📍 PUBLIC URLs")
    print("-" * 70)
    for url_name, description in test_urls:
        try:
            url = reverse(url_name)
            response = client.get(url)
            status = response.status_code
            result = "✅" if status == 200 else f"⚠️  ({status})"
            print(f"{result} {description:.<50} {url}")
        except Exception as e:
            print(f"❌ {description:.<50} ERROR: {str(e)[:30]}")
    
    print("\n📍 STAFF/ADMIN URLs")
    print("-" * 70)
    for url_name, description in staff_urls:
        try:
            url = reverse(url_name)
            # These will redirect to login, which is expected (302)
            response = client.get(url, follow=False)
            status = response.status_code
            result = "✅" if status in [200, 302] else f"⚠️  ({status})"
            print(f"{result} {description:.<50} {url}")
        except Exception as e:
            print(f"❌ {description:.<50} ERROR: {str(e)[:30]}")
    
    print("\n" + "=" * 70)
    print("✅ URL ROUTING VERIFICATION COMPLETE")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    test_urls()
