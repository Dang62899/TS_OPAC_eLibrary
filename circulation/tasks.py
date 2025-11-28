from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.utils.html import strip_tags
from datetime import timedelta
from .models import Loan, Hold, Notification
import logging
import traceback

def send_notification_email(notification):
    """
    Send email for a notification
    Returns True if successful, False otherwise
    """
    try:
        # Get email template based on notification type
        html_content = render_to_string('circulation/emails/notification_email.html', {
            'notification': notification,
            'borrower': notification.borrower,
            'loan': notification.loan,
            'hold': notification.hold,
            'site_name': getattr(settings, 'LIBRARY_NAME', 'e-Library'),
        })

        # Create plain text version
        text_content = strip_tags(html_content)

        # Create email
        email = EmailMultiAlternatives(
            subject=notification.title,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[notification.borrower.email],
        )
        email.attach_alternative(html_content, "text/html")

        # Send email
        email.send()

        # Mark as sent
        notification.email_sent = True
        notification.email_sent_date = timezone.now()
        notification.save()

        return True

    except Exception as e:
        logger = logging.getLogger(__name__)
        tb = traceback.format_exc()
        logger.exception("Failed to send notification email %s: %s", notification.id, e)
        notification.email_error = tb
        notification.save()
        return False

@shared_task
def send_pending_notification_emails():
    """
    Celery task to send all pending notification emails
    Runs every 5 minutes
    """
    pending_notifications = Notification.objects.filter(
        email_sent=False,
        borrower__email__isnull=False
    ).exclude(borrower__email='')[:50]  # Limit to 50 per run

    sent_count = 0
    for notification in pending_notifications:
        if send_notification_email(notification):
            sent_count += 1

    return f"Sent {sent_count} notification emails"

@shared_task
def check_due_soon_items():
    """
    Check for items due in 3 days and create notifications
    Runs daily
    """
    three_days_from_now = timezone.now().date() + timedelta(days=3)

    due_soon_loans = Loan.objects.filter(
        status='active',
        due_date=three_days_from_now
    ).select_related('borrower', 'item__publication')

    created_count = 0
    for loan in due_soon_loans:
        # Check if notification already exists
        existing = Notification.objects.filter(
            borrower=loan.borrower,
            loan=loan,
            notification_type='due_soon',
            created_date__gte=timezone.now() - timedelta(days=1)
        ).exists()

        if not existing:
            Notification.objects.create(
                borrower=loan.borrower,
                loan=loan,
                notification_type='due_soon',
                title=f'Item Due Soon: {loan.item.publication.title}',
                message=f'Your borrowed item "{loan.item.publication.title}" is due on {loan.due_date}. Please return it on time to avoid late fees.',
                action_url='/accounts/my-account/'
            )
            created_count += 1

    return f"Created {created_count} due-soon notifications"

@shared_task
def check_overdue_items():
    """
    Check for overdue items and create notifications
    Runs daily
    """
    today = timezone.now().date()
    overdue_loans = Loan.objects.filter(
        status='active',
        due_date__lt=today
    ).select_related('borrower', 'item__publication')

    created_count = 0
    for loan in overdue_loans:
        days_overdue = (today - loan.due_date).days

        # Send notification every 7 days
        if days_overdue % 7 == 0:
            # Check if we already sent one today
            existing = Notification.objects.filter(
                borrower=loan.borrower,
                loan=loan,
                notification_type='overdue',
                created_date__gte=timezone.now() - timedelta(hours=23)
            ).exists()

            if not existing:
                Notification.objects.create(
                    borrower=loan.borrower,
                    loan=loan,
                    notification_type='overdue',
                    title=f'Overdue: {loan.item.publication.title}',
                    message=f'Your item "{loan.item.publication.title}" is {days_overdue} days overdue. Please return it immediately to avoid additional fees.',
                    action_url='/accounts/my-account/'
                )
                created_count += 1

    return f"Created {created_count} overdue notifications"

@shared_task
def check_expiring_holds():
    """
    Check for holds expiring soon and create notifications
    Runs daily
    """
    tomorrow = timezone.now() + timedelta(days=1)

    expiring_holds = Hold.objects.filter(
        status='ready',
        expiry_date__lte=tomorrow,
        expiry_date__gte=timezone.now()
    ).select_related('borrower', 'publication')

    created_count = 0
    for hold in expiring_holds:
        # Check if notification already exists
        existing = Notification.objects.filter(
            borrower=hold.borrower,
            hold=hold,
            notification_type='hold_expiring',
            created_date__gte=timezone.now() - timedelta(days=1)
        ).exists()

        if not existing:
            Notification.objects.create(
                borrower=hold.borrower,
                hold=hold,
                notification_type='hold_expiring',
                title=f'Hold Expiring Soon: {hold.publication.title}',
                message=f'Your hold for "{hold.publication.title}" will expire on {hold.expiry_date.strftime("%Y-%m-%d")}. Please pick it up soon.',
                action_url='/accounts/my-account/'
            )
            created_count += 1

    return f"Created {created_count} expiring hold notifications"
