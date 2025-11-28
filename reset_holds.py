import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elibrary.settings')
django.setup()

from circulation.models import Hold

# Reset the incorrectly marked "ready" holds back to "waiting"
for hold in Hold.objects.filter(status='ready'):
    hold.status = 'waiting'
    hold.save()
    print(f'Reset hold {hold.id} ({hold.publication.title}) to waiting')

print('\nDone! Holds reset to waiting status.')
