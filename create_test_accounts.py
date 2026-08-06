import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elibrary.settings')
import django
django.setup()
from accounts.models import User

accounts = [
    ('admin_test', 'admin@example.com', 'AdminPass123!', 'admin'),
    ('staff_test', 'staff@example.com', 'StaffPass123!', 'staff'),
    ('borrower_test', 'borrower@example.com', 'BorrowerPass123!', 'borrower'),
]

for username, email, password, user_type in accounts:
    user = User.objects.filter(username=username).first()
    if user is None:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            user_type=user_type,
        )
        created = True
    else:
        user.set_password(password)
        user.email = email
        user.user_type = user_type
        user.is_staff = user_type in {'staff', 'admin'}
        user.is_superuser = user_type == 'admin'
        user.save()
        created = False

    print(f"{username} / {password} / {user_type} ({'created' if created else 'updated'})")
