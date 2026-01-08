from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(username='admin')
user.set_password('admin123456')
user.save()
print("✓ Admin password set to: admin123456")
