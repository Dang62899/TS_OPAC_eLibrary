import os
from .celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "elibrary.settings")

app = Celery("elibrary")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    # Send notification emails every 5 minutes
    "send-pending-notifications": {
        "task": "circulation.tasks.send_pending_notification_emails",
        "schedule": 300.0,  # Every 5 minutes (in seconds)
    },
    # Check for due-soon items daily at 9 AM
    "check-due-soon-items-daily": {
        "task": "circulation.tasks.check_due_soon_items",
        "schedule": crontab(hour=9, minute=0),  # Run daily at 9 AM
    },
    # Check for overdue items daily at 10 AM
    "check-overdue-items-daily": {
        "task": "circulation.tasks.check_overdue_items",
        "schedule": crontab(hour=10, minute=0),  # Run daily at 10 AM
    },
    # Check for expiring holds daily at 11 AM
    "check-expiring-holds-daily": {
        "task": "circulation.tasks.check_expiring_holds",
        "schedule": crontab(hour=11, minute=0),  # Run daily at 11 AM
    },
}
