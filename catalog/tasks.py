from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone


@shared_task
def send_otp_email(otp_id):
    from .models import DownloadOTP

    try:
        otp = DownloadOTP.objects.get(id=otp_id)
    except DownloadOTP.DoesNotExist:
        return

    recipient = otp.user.email if otp.user and otp.user.email else None
    if not recipient:
        return

    subject = f"Elibrary: download code for {otp.attachment.publication.title}"
    body = render_to_string("catalog/otp_email.txt", {"otp": otp, "attachment": otp.attachment})
    send_mail(subject, body, getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"), [recipient])


@shared_task
def purge_expired_view_logs():
    from .models import ViewLog

    retention_days = max(1, int(getattr(settings, "VIEW_LOG_RETENTION_DAYS", 365)))
    cutoff = timezone.now() - timezone.timedelta(days=retention_days)
    deleted_count, _ = ViewLog.objects.filter(timestamp__lt=cutoff).delete()
    return deleted_count
