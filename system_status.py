import os
import django


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "elibrary.settings")
    django.setup()

    from django.contrib.auth import get_user_model
    from catalog.models import Publication, Item
    from circulation.models import CheckoutRequest, Hold

    User = get_user_model()

    print("=== CURRENT SYSTEM STATE ===\n")

    # Get users
    student = User.objects.get(username="student")
    admin = User.objects.get(username="admin")

    print(f"Students: {student.username} ({student.email})")
    print(f"Staff: {admin.username} ({admin.email})")

    print("\n=== PUBLICATIONS WITH TEST DATA ===\n")
    for pub_id in [44, 45, 46, 47, 48]:
        try:
            pub = Publication.objects.get(id=pub_id)
            items = Item.objects.filter(publication=pub)
            available_count = items.filter(status="available").count()
            on_loan_count = items.filter(status="on_loan").count()
            on_shelf_count = items.filter(status="on_hold_shelf").count()

            print(f"📚 {pub.title}")
            print(
                f"   Total: {items.count()} | Available: {available_count} | On Loan: {on_loan_count} | Hold Shelf: {on_shelf_count}"
            )
            for item in items:
                # Show Item ID and barcode if present
                barcode_display = item.barcode if getattr(item, "barcode", None) else "N/A"
                print(f"      - ID {item.id} | Barcode: {barcode_display} | Status: {item.status}")
            print()
        except Publication.DoesNotExist:
            print(f"Publication {pub_id} not found")

    print("\n=== CHECKOUT REQUESTS ===\n")
    requests = CheckoutRequest.objects.all()
    if requests.exists():
        for req in requests:
            print(f"ID: {req.id} | {req.publication.title} | Status: {req.status} | Borrower: {req.borrower.username}")
    else:
        print("No checkout requests")

    print("\n=== HOLDS ===\n")
    holds = Hold.objects.all()
    if holds.exists():
        for hold in holds:
            print(
                f"ID: {hold.id} | {hold.publication.title} | Status: {hold.status} | Borrower: {hold.borrower.username}"
            )
    else:
        print("No holds")

    print("\n=== RECOMMENDED TESTS ===\n")
    print("1. Test Checkout Request Workflow:")
    print("   - Login as student")
    print("   - Go to Publication 44 (Available Book)")
    print("   - Click 'Request This Book'")
    print("   - Login as admin → approve request")
    print("   - Login as admin → complete pickup (select AVAIL-001)")
    print()
    print("2. Test Hold Workflow:")
    print("   - Login as student")
    print("   - Go to Publication 46 or 48 (Unavailable Books)")
    print("   - Click 'Place Hold'")
    print("   - Login as admin → try 'Set Ready' (should fail - no items available)")
    print("   - Login as admin → check in one of the items")
    print("   - Hold should automatically become 'ready'")
    print("   - Login as admin → complete pickup")
    print()
    print("3. Test Manual Hold Ready:")
    print("   - Login as student → Place hold on Publication 46")
    print("   - Login as admin → Go to Manage Holds")
    print("   - Try to set hold ready (should fail - no items available)")
    print("   - This proves the fix works!")


if __name__ == "__main__":
    main()
