#!/usr/bin/env bash
# Render build script
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input

# Create the first admin from env vars (only if it does not exist yet)
python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model

username = os.environ.get("ADMIN_USERNAME")
password = os.environ.get("ADMIN_PASSWORD")
if username and password:
    User = get_user_model()
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(
            username=username,
            email=os.environ.get("ADMIN_EMAIL", ""),
            password=password,
            user_type="admin",
        )
        print("Created admin user", username)
PY
