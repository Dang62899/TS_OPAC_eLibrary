from django.contrib import admin
from .models import Loan, Hold, InTransit, Notification, CheckoutRequest

@admin.register(Loan)


class LoanAdmin(admin.ModelAdmin):
    list_display = ['item', 'borrower', 'checkout_date', 'due_date', 'return_date', 'status', 'renewal_count']
    list_filter = ['status', 'checkout_date', 'due_date']
    search_fields = ['item__barcode', 'borrower__username', 'borrower__email']
    readonly_fields = ['checkout_date']

    fieldsets = (
        ('Loan Information', {
            'fields': ('item', 'borrower', 'status')
        }),
        ('Dates', {
            'fields': ('checkout_date', 'due_date', 'return_date', 'renewal_count')
        }),
        ('Staff', {
            'fields': ('checkout_staff', 'return_staff')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )

@admin.register(Hold)


class HoldAdmin(admin.ModelAdmin):
    list_display = ['publication', 'borrower', 'hold_date', 'status', 'queue_position', 'pickup_location']
    list_filter = ['status', 'hold_date', 'pickup_location']
    search_fields = ['publication__title', 'borrower__username', 'borrower__email']
    readonly_fields = ['hold_date', 'ready_date']

@admin.register(InTransit)


class InTransitAdmin(admin.ModelAdmin):
    list_display = ['item', 'from_location', 'to_location', 'send_date', 'receive_date', 'status']
    list_filter = ['status', 'from_location', 'to_location']
    search_fields = ['item__barcode', 'item__publication__title']
    readonly_fields = ['send_date']

@admin.register(Notification)


class NotificationAdmin(admin.ModelAdmin):
    list_display = ['borrower', 'notification_type', 'title', 'created_date', 'is_read', 'email_sent']
    list_filter = ['notification_type', 'is_read', 'email_sent', 'created_date']
    search_fields = ['borrower__username', 'borrower__email', 'title', 'message']
    readonly_fields = ['created_date', 'read_date', 'email_sent_date']

    fieldsets = (
        ('Notification Info', {
            'fields': ('borrower', 'notification_type', 'title', 'message')
        }),
        ('Related Objects', {
            'fields': ('loan', 'hold', 'action_url')
        }),
        ('Read Status', {
            'fields': ('is_read', 'read_date', 'created_date')
        }),
        ('Email Status', {
            'fields': ('email_sent', 'email_sent_date', 'email_error')
        }),
    )

@admin.register(CheckoutRequest)


class CheckoutRequestAdmin(admin.ModelAdmin):
    list_display = ['publication', 'borrower', 'request_date', 'status', 'reviewed_by', 'pickup_location']
    list_filter = ['status', 'request_date', 'pickup_location']
    search_fields = ['publication__title', 'borrower__username', 'borrower__email']
    readonly_fields = ['request_date', 'review_date']

    fieldsets = (
        ('Request Info', {
            'fields': ('publication', 'borrower', 'request_date', 'status', 'notes')
        }),
        ('Staff Review', {
            'fields': ('reviewed_by', 'review_date', 'staff_notes')
        }),
        ('Pickup Details', {
            'fields': ('pickup_location', 'pickup_by_date')
        }),
        ('Completed Loan', {
            'fields': ('loan',)
        }),
    )
