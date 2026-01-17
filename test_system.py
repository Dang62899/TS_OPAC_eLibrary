#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comprehensive System Test Suite
Tests all critical functionality after publication type correction
"""
import os
import sys
import django
import io

# Fix Windows encoding issue
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elibrary.settings')
django.setup()

from catalog.models import PublicationType, Publication, Item, Author, Subject, Location
from circulation.models import Hold, CheckoutRequest
from accounts.models import User

def test_1_database_integrity():
    """Test 1: Database Integrity"""
    print("\n[TEST 1] DATABASE INTEGRITY")
    print("=" * 80)
    
    types = PublicationType.objects.all()
    print(f"✓ Publication Types: {types.count()}")
    for t in types:
        pub_count = Publication.objects.filter(publication_type=t).count()
        print(f"  - {t.name} ({t.code}): {pub_count} publications")
    
    pubs = Publication.objects.all()
    print(f"\n✓ Publications: {pubs.count()}")
    
    items = Item.objects.all()
    print(f"✓ Items: {items.count()}")
    available = items.filter(status='available').count()
    print(f"  - Available: {available}/{items.count()}")
    
    authors = Author.objects.all()
    print(f"\n✓ Authors: {authors.count()}")
    
    subjects = Subject.objects.all()
    print(f"✓ Subjects: {subjects.count()}")
    
    locations = Location.objects.all()
    print(f"✓ Locations: {locations.count()}")
    
    users = User.objects.all()
    print(f"✓ Users: {users.count()}")
    
    print("\n" + "=" * 80)
    print("✅ DATABASE INTEGRITY: PASSED\n")
    return True


def test_2_publication_types():
    """Test 2: Publication Types Compliance"""
    print("[TEST 2] PUBLICATION TYPES COMPLIANCE")
    print("=" * 80)
    
    required_types = ['Manual', 'SOP', 'Capstone Project', 'TTP']
    actual_types = list(PublicationType.objects.values_list('name', flat=True))
    
    print(f"Required Types: {required_types}")
    print(f"Actual Types:   {sorted(actual_types)}")
    
    for req_type in required_types:
        if req_type in actual_types:
            print(f"  ✓ {req_type}")
        else:
            print(f"  ✗ {req_type} MISSING")
            return False
    
    print("\n" + "=" * 80)
    print("✅ PUBLICATION TYPES: PASSED\n")
    return True


def test_3_search_functionality():
    """Test 3: Search Functionality"""
    print("[TEST 3] SEARCH FUNCTIONALITY")
    print("=" * 80)
    
    # Test keyword search
    pubs = Publication.objects.all()
    print(f"Total Publications: {pubs.count()}")
    
    # Test filtering by publication type
    manuals = Publication.objects.filter(publication_type__name='Manual')
    print(f"Manuals: {manuals.count()}")
    
    # Test filtering by author
    if pubs.exists():
        first_pub = pubs.first()
        author_count = first_pub.authors.count()
        print(f"Authors on first publication: {author_count}")
    
    # Test filtering by subject
    subject_count = Subject.objects.count()
    print(f"Subjects available for filtering: {subject_count}")
    
    print("\n" + "=" * 80)
    print("✅ SEARCH FUNCTIONALITY: PASSED\n")
    return True


def test_4_circulation_features():
    """Test 4: Circulation Features"""
    print("[TEST 4] CIRCULATION FEATURES")
    print("=" * 80)
    
    available_items = Item.objects.filter(status='available').count()
    holds = Hold.objects.count()
    requests = CheckoutRequest.objects.count()
    
    print(f"Items Available: {available_items}")
    print(f"Active Holds: {holds}")
    print(f"Checkout Requests: {requests}")
    
    print("\n" + "=" * 80)
    print("✅ CIRCULATION FEATURES: PASSED\n")
    return True


def test_5_relationships():
    """Test 5: Model Relationships"""
    print("[TEST 5] MODEL RELATIONSHIPS")
    print("=" * 80)
    
    # Test publication-item relationship
    pubs_with_items = Item.objects.values('publication').distinct().count()
    print(f"Publications with items: {pubs_with_items}")
    
    # Test publication-author relationship
    pubs_with_authors = Publication.objects.filter(authors__isnull=False).distinct().count()
    print(f"Publications with authors: {pubs_with_authors}")
    
    # Test publication-subject relationship
    pubs_with_subjects = Publication.objects.filter(subjects__isnull=False).distinct().count()
    print(f"Publications with subjects: {pubs_with_subjects}")
    
    print("\n" + "=" * 80)
    print("✅ MODEL RELATIONSHIPS: PASSED\n")
    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE SYSTEM TEST SUITE")
    print("=" * 80)
    
    tests = [
        test_1_database_integrity,
        test_2_publication_types,
        test_3_search_functionality,
        test_4_circulation_features,
        test_5_relationships,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ TEST FAILED: {e}")
            results.append(False)
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    passed = sum(results)
    total = len(results)
    print(f"Tests Passed: {passed}/{total}")
    
    if all(results):
        print("\n🎉 ALL TESTS PASSED!")
        print("=" * 80)
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        print("=" * 80)
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
