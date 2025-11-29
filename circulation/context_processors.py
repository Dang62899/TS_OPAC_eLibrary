from circulation.models import Notification


def unread_notifications(request):
    """
    Add unread notification count to template context
    """
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            borrower=request.user,
            is_read=False
        ).count()

        recent_notifications = Notification.objects.filter(
            borrower=request.user
        ).select_related('loan__item__publication', 'hold__publication').order_by('-created_date')[:5]

        return {
            'unread_notifications_count': unread_count,
            'recent_notifications': recent_notifications,
        }
    return {
        'unread_notifications_count': 0,
        'recent_notifications': [],
    }
