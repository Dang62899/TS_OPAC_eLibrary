from django.contrib import admin
from .models import Loan, Hold, InTransit, Notification, CheckoutRequest, NotificationPreference, NotificationArchive, ActivityLog, SystemHealth, BackupLog


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ["item", "borrower", "checkout_date", "due_date", "return_date", "status", "renewal_count"]
    list_filter = ["status", "checkout_date", "due_date"]
    search_fields = ["item__barcode", "borrower__username", "borrower__email"]
    readonly_fields = ["checkout_date"]

    fieldsets = (
        ("Loan Information", {"fields": ("item", "borrower", "status")}),
        ("Dates", {"fields": ("checkout_date", "due_date", "return_date", "renewal_count")}),
        ("Staff", {"fields": ("checkout_staff", "return_staff")}),
        ("Notes", {"fields": ("notes",)}),
    )


@admin.register(Hold)
class HoldAdmin(admin.ModelAdmin):
    list_display = ["publication", "borrower", "hold_date", "status", "queue_position", "pickup_location"]
    list_filter = ["status", "hold_date", "pickup_location"]
    search_fields = ["publication__title", "borrower__username", "borrower__email"]
    readonly_fields = ["hold_date", "ready_date"]


@admin.register(InTransit)
class InTransitAdmin(admin.ModelAdmin):
    list_display = ["item", "from_location", "to_location", "send_date", "receive_date", "status"]
    list_filter = ["status", "from_location", "to_location"]
    search_fields = ["item__barcode", "item__publication__title"]
    readonly_fields = ["send_date"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["borrower", "notification_type", "title", "created_date", "is_read", "email_sent"]
    list_filter = ["notification_type", "is_read", "email_sent", "created_date"]
    search_fields = ["borrower__username", "borrower__email", "title", "message"]
    readonly_fields = ["created_date", "read_date", "email_sent_date"]

    fieldsets = (
        ("Notification Info", {"fields": ("borrower", "notification_type", "title", "message")}),
        ("Related Objects", {"fields": ("loan", "hold", "action_url")}),
        ("Read Status", {"fields": ("is_read", "read_date", "created_date")}),
        ("Email Status", {"fields": ("email_sent", "email_sent_date", "email_error")}),
    )


@admin.register(CheckoutRequest)
class CheckoutRequestAdmin(admin.ModelAdmin):
    list_display = ["publication", "borrower", "request_date", "status", "reviewed_by", "pickup_location"]
    list_filter = ["status", "request_date", "pickup_location"]
    search_fields = ["publication__title", "borrower__username", "borrower__email"]
    readonly_fields = ["request_date", "review_date"]

    fieldsets = (
        ("Request Info", {"fields": ("publication", "borrower", "request_date", "status", "notes")}),
        ("Staff Review", {"fields": ("reviewed_by", "review_date", "staff_notes")}),
        ("Pickup Details", {"fields": ("pickup_location", "pickup_by_date")}),
        ("Completed Loan", {"fields": ("loan",)}),
    )


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ["borrower", "default_channel", "enable_sound_alerts", "enable_email_digest", "email_digest_frequency"]
    list_filter = ["default_channel", "enable_sound_alerts", "enable_email_digest", "email_digest_frequency"]
    search_fields = ["borrower__username", "borrower__email"]

    fieldsets = (
        ("User", {"fields": ("borrower",)}),
        ("Notification Types", {
            "fields": (
                "checkout_notification", "checkin_notification", "due_soon_notification",
                "overdue_notification", "hold_ready_notification", "hold_placed_notification",
                "hold_expiring_notification", "renewal_notification", "fine_notification"
            )
        }),
        ("Channel Preferences", {"fields": ("default_channel",)}),
        ("Sound Alerts", {"fields": ("enable_sound_alerts", "sound_volume")}),
        ("Email Digest", {"fields": ("enable_email_digest", "email_digest_frequency", "last_digest_sent")}),
        ("Quiet Hours", {"fields": ("quiet_hours_enabled", "quiet_hours_start", "quiet_hours_end")}),
    )


@admin.register(NotificationArchive)
class NotificationArchiveAdmin(admin.ModelAdmin):
    list_display = ["borrower", "notification_type", "title", "created_date", "archived_date"]
    list_filter = ["notification_type", "archived_date"]
    search_fields = ["borrower__username", "title", "message"]
    readonly_fields = ["created_date", "archived_date"]


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ["user", "action", "description", "timestamp", "success", "ip_address"]
    list_filter = ["action", "success", "timestamp"]
    search_fields = ["user__username", "description", "ip_address"]
    readonly_fields = ["timestamp", "user", "action", "description", "content_type", "object_id", "object_repr", "ip_address", "user_agent", "success", "error_message"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(SystemHealth)
class SystemHealthAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "status", "cpu_usage_percent", "memory_usage_percent", "disk_usage_percent", "error_count"]
    list_filter = ["status", "timestamp"]
    readonly_fields = ["timestamp", "database_size_mb", "active_connections", "cpu_usage_percent", "memory_usage_percent", "disk_usage_percent", "active_users", "total_requests", "failed_requests", "average_response_time_ms", "cache_hits", "cache_misses", "error_count", "warning_count"]

    fieldsets = (
        ("Timestamp", {"fields": ("timestamp",)}),
        ("Database Metrics", {"fields": ("database_size_mb", "active_connections", "slow_queries")}),
        ("Server Metrics", {"fields": ("cpu_usage_percent", "memory_usage_percent", "disk_usage_percent")}),
        ("Application Metrics", {"fields": ("active_users", "total_requests", "failed_requests", "average_response_time_ms")}),
        ("Cache Metrics", {"fields": ("cache_hits", "cache_misses")}),
        ("Error Tracking", {"fields": ("error_count", "warning_count")}),
        ("Status", {"fields": ("status", "notes")}),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BackupLog)
class BackupLogAdmin(admin.ModelAdmin):
    list_display = ["backup_type", "status", "start_time", "end_time", "backup_size_mb", "backup_location", "created_by"]
    list_filter = ["backup_type", "status", "start_time"]
    search_fields = ["backup_path", "created_by__username"]
    readonly_fields = ["start_time", "end_time"]

    fieldsets = (
        ("Backup Info", {"fields": ("backup_type", "status", "backup_location")}),
        ("Timing", {"fields": ("start_time", "end_time")}),
        ("Size & Files", {"fields": ("backup_size_mb", "files_backed_up")}),
        ("Storage", {"fields": ("backup_path",)}),
        ("Creator", {"fields": ("created_by",)}),
        ("Status", {"fields": ("error_message", "notes")}),
    )

