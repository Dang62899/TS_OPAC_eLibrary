import os
import django


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elibrary.settings')
    django.setup()

    from catalog.models import Item
    from circulation.models import CheckoutRequest, Hold

    print('=== ALL HOLDS ===')
    for hold in Hold.objects.all():
        print(f'  ID: {hold.id}, Publication: {hold.publication.title}, Status: {hold.status}')

    # Check ready holds
    ready_hold = Hold.objects.filter(status='ready').first()
    if ready_hold:
        print(f'\n=== Ready Hold ID: {ready_hold.id} ===')
        print(f'Publication: {ready_hold.publication.title}')
        print(f'Borrower: {ready_hold.borrower.username}')
        print(f'Pickup Location: {ready_hold.pickup_location}')

        print('\nAll items for this publication:')
        items = Item.objects.filter(publication=ready_hold.publication)
        print(f'Total items: {items.count()}')
        for item in items:
                print(f'  - Item ID: {item.barcode}, Status: {item.status}')

        print('\nItems matching query (available or on_hold_shelf):')
        available_items = items.filter(status__in=['available', 'on_hold_shelf'])
        print(f'Count: {available_items.count()}')
        for item in available_items:
            print(f'  - Item ID: {item.barcode}, Status: {item.status}')
    else:
        print('\nNo ready holds found')

    print('\n=== ALL CHECKOUT REQUESTS ===')
    for req in CheckoutRequest.objects.all():
        print(f'  ID: {req.id}, Publication: {req.publication.title}, Status: {req.status}')


if __name__ == '__main__':
    main()
