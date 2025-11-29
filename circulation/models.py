from django.db import models
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from catalog.models import Item, Publication


class Loan(models.Model):
    """Record of item checkout/loan"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
        ('overdue_returned', 'Overdue (Returned)'),
        ('lost', 'Lost'),
    ]

    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='loans')
    borrower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='loans')
    checkout_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateField()
    return_date = models.DateTimeField(null=True, blank=True)
    renewal_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)

    # Staff who processed the transaction
    checkout_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checkouts_processed'
    )
    return_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='returns_processed'
    )

    class Meta:
        ordering = ['-checkout_date']
        indexes = [
            models.Index(fields=['borrower', 'status']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        return f"{self.item} - {self.borrower} ({self.status})"

    def save(self, *args, **kwargs):
        # Set due date if not set
        if not self.due_date:
            self.due_date = (timezone.now() + timedelta(days=settings.LOAN_PERIOD_DAYS)).date()

        # Update item status
        if self.status == 'active' and not self.return_date:
            self.item.status = 'on_loan'
            self.item.save()
        elif self.status in ['returned', 'overdue_returned'] and self.return_date:
            self.item.status = 'available'
            self.item.save()

        super().save(*args, **kwargs)

    def is_overdue(self):
        """Check if loan is overdue"""
        if self.status == 'active' and not self.return_date:
            return timezone.now().date() > self.due_date
        return False

    def days_overdue(self):
        """Calculate days overdue"""
        if self.is_overdue():
            return (timezone.now().date() - self.due_date).days
        return 0

    def can_renew(self):
        """Check if loan can be renewed"""
        if self.renewal_count >= settings.RENEWAL_LIMIT:
            return False
        if self.is_overdue():
            return False
        # Check if there are holds on this item
        if Hold.objects.filter(publication=self.item.publication, status='waiting').exists():
            return False
        return True

    def renew(self):
        """Renew the loan"""
        if self.can_renew():
            self.due_date = self.due_date + timedelta(days=settings.LOAN_PERIOD_DAYS)
            self.renewal_count += 1
            self.save()
            return True
        return False


class Hold(models.Model):
    """Hold/reserve request for a publication"""
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('ready', 'Ready for Pickup'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]

    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='holds')
    borrower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='holds')
    hold_date = models.DateTimeField(default=timezone.now)
    ready_date = models.DateTimeField(null=True, blank=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    pickup_location = models.ForeignKey(
        'catalog.Location',
        on_delete=models.PROTECT,
        related_name='holds'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    queue_position = models.IntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['hold_date']
        indexes = [
            models.Index(fields=['borrower', 'status']),
            models.Index(fields=['publication', 'status']),
        ]

    def __str__(self):
        return f"{self.publication} - {self.borrower} ({self.status})"

    def save(self, *args, **kwargs):
        # Set expiry date when status changes to ready
        if self.status == 'ready' and not self.ready_date:
            self.ready_date = timezone.now()
            self.expiry_date = timezone.now() + timedelta(days=7)

        super().save(*args, **kwargs)

    def update_queue_position(self):
        """Update position in queue"""
        waiting_holds = Hold.objects.filter(
            publication=self.publication,
            status='waiting',
            hold_date__lt=self.hold_date
        ).count()
        self.queue_position = waiting_holds + 1
        self.save()


class InTransit(models.Model):
    """Track items in transit between locations"""
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='transits')
    from_location = models.ForeignKey(
        'catalog.Location',
        on_delete=models.PROTECT,
        related_name='transits_from'
    )
    to_location = models.ForeignKey(
        'catalog.Location',
        on_delete=models.PROTECT,
        related_name='transits_to'
    )
    send_date = models.DateTimeField(default=timezone.now)
    receive_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('in_transit', 'In Transit'),
            ('received', 'Received'),
        ],
        default='in_transit'
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-send_date']
        verbose_name_plural = 'Items in transit'

    def __str__(self):
        return f"{self.item} - {self.from_location} to {self.to_location}"

    def mark_received(self):
        """Mark item as received"""
        self.status = 'received'
        self.receive_date = timezone.now()
        self.item.location = self.to_location
        self.item.status = 'available'
        self.item.save()
        self.save()


class Notification(models.Model):
    """User notifications for in-app and email alerts"""
    NOTIFICATION_TYPES = [
        ('checkout', 'Item Checked Out'),
        ('checkin', 'Item Returned'),
        ('due_soon', 'Due Soon (3 days)'),
        ('overdue', 'Overdue Notice'),
        ('hold_ready', 'Hold Ready for Pickup'),
        ('hold_placed', 'Hold Placed Successfully'),
        ('hold_expiring', 'Hold Expiring Soon'),
        ('hold_cancelled', 'Hold Cancelled'),
        ('renewal', 'Item Renewed'),
        ('fine_added', 'Fine Added'),
    ]

    borrower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200, default='Notification')
    message = models.TextField(default='You have a new notification.')

    # Related objects
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    hold = models.ForeignKey(Hold, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')

    # Notification tracking
    created_date = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    read_date = models.DateTimeField(null=True, blank=True)

    # Email tracking
    email_sent = models.BooleanField(default=False)
    email_sent_date = models.DateTimeField(null=True, blank=True)
    email_error = models.TextField(blank=True)

    # Action URL (optional - for "View Details" button)
    action_url = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ['-created_date']
        indexes = [
            models.Index(fields=['borrower', 'is_read']),
            models.Index(fields=['created_date']),
        ]

    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.borrower}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_date = timezone.now()
            self.save()

    def get_icon(self):
        """Return Bootstrap icon for notification type"""
        icons = {
            'checkout': 'book-half',
            'checkin': 'check-circle',
            'due_soon': 'clock',
            'overdue': 'exclamation-triangle',
            'hold_ready': 'bookmark-check',
            'hold_placed': 'bookmark-plus',
            'hold_expiring': 'hourglass-split',
            'hold_cancelled': 'bookmark-x',
            'renewal': 'arrow-repeat',
            'fine_added': 'cash',
        }
        return icons.get(self.notification_type, 'bell')

    def get_css_class(self):
        """Return CSS class for notification styling"""
        classes = {
            'checkout': 'primary',
            'checkin': 'success',
            'due_soon': 'warning',
            'overdue': 'danger',
            'hold_ready': 'success',
            'hold_placed': 'info',
            'hold_expiring': 'warning',
            'hold_cancelled': 'secondary',
            'renewal': 'info',
            'fine_added': 'warning',
        }
        return classes.get(self.notification_type, 'info')


class CheckoutRequest(models.Model):
    """User request to checkout a book (instead of going to library)"""
    STATUS_CHOICES = [
        ('pending', 'Pending Staff Approval'),
        ('approved', 'Approved - Ready for Pickup'),
        ('completed', 'Completed - Checked Out'),
        ('cancelled', 'Cancelled'),
        ('denied', 'Denied'),
    ]

    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='checkout_requests')
    borrower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='checkout_requests')
    request_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, help_text='Optional notes from borrower')

    # Staff response
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_checkout_requests'
    )
    review_date = models.DateTimeField(null=True, blank=True)
    staff_notes = models.TextField(blank=True, help_text='Staff notes/reason for denial')

    # Pickup details
    pickup_location = models.ForeignKey(
        'catalog.Location',
        on_delete=models.PROTECT,
        related_name='checkout_requests',
        null=True,
        blank=True
    )
    pickup_by_date = models.DateTimeField(null=True, blank=True, help_text='Borrower must pick up by this date')

    # Linked loan (when completed)
    loan = models.OneToOneField(Loan, on_delete=models.SET_NULL, null=True, blank=True, related_name='checkout_request')
    # Reserved item (optional) - set when staff approves the request to prevent double-allocation
    reserved_item = models.ForeignKey(
        'catalog.Item',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reserved_for_requests'
    )

    class Meta:
        ordering = ['-request_date']
        indexes = [
            models.Index(fields=['borrower', 'status']),
            models.Index(fields=['status', 'request_date']),
        ]

    def __str__(self):
        return f"{self.publication.title} - {self.borrower.username} ({self.status})"

    def can_be_approved(self):
        """Check if request can be approved"""
        if self.status != 'pending':
            return False
        # Check if there's an available copy
        available_items = self.publication.items.filter(status='available')
        return available_items.exists()
