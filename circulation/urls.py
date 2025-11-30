from django.urls import path
from . import views

app_name = "circulation"

urlpatterns = [
    # Dashboards - Role-based
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("staff-dashboard/", views.staff_dashboard, name="staff_dashboard"),
    # Checkout/Checkin
    path("checkout/", views.checkout, name="checkout"),
    path("checkin/", views.checkin, name="checkin"),
    # Renewals
    path("renew/<int:loan_id>/", views.renew_loan, name="renew_loan"),
    path("renew-online/<int:loan_id>/", views.renew_loan_online, name="renew_loan_online"),
    # Holds
    path("hold/place/<int:publication_id>/", views.place_hold, name="place_hold"),
    path("hold/cancel/<int:hold_id>/", views.cancel_hold, name="cancel_hold"),
    path("holds/manage/", views.manage_holds, name="manage_holds"),
    path("hold/set-ready/<int:hold_id>/", views.set_hold_ready, name="set_hold_ready"),
    path("hold/complete/<int:hold_id>/", views.complete_hold, name="complete_hold"),
    # Borrower Management
    path("borrowers/", views.borrower_list, name="borrower_list"),
    path("borrower/<int:user_id>/", views.borrower_detail, name="borrower_detail"),
    path("borrower/<int:user_id>/block/", views.block_borrower, name="block_borrower"),
    path("borrower/<int:user_id>/unblock/", views.unblock_borrower, name="unblock_borrower"),
    # In-Transit
    path("transit/send/", views.send_in_transit, name="send_in_transit"),
    path("transit/receive/", views.receive_in_transit, name="receive_in_transit"),
    path("transit/list/", views.transit_list, name="transit_list"),
    # Reports
    path("reports/", views.reports, name="reports"),
    path("reports/overdue/", views.overdue_report, name="overdue_report"),
    path("reports/circulation-stats/", views.circulation_stats, name="circulation_stats"),
    # Notifications
    path("notifications/", views.notifications_list, name="notifications_list"),
    path("notifications/<int:notification_id>/read/", views.mark_notification_read, name="mark_notification_read"),
    path("notifications/read-all/", views.mark_all_notifications_read, name="mark_all_notifications_read"),
    path("notifications/<int:notification_id>/delete/", views.delete_notification, name="delete_notification"),
    # Checkout Requests
    path("checkout-request/<int:publication_id>/", views.request_checkout, name="request_checkout"),
    path("checkout-request/<int:request_id>/cancel/", views.cancel_checkout_request, name="cancel_checkout_request"),
    path("checkout-requests/", views.manage_checkout_requests, name="manage_checkout_requests"),
    path("checkout-request/<int:request_id>/approve/", views.approve_checkout_request, name="approve_checkout_request"),
    path("checkout-request/<int:request_id>/deny/", views.deny_checkout_request, name="deny_checkout_request"),
    path(
        "checkout-request/<int:request_id>/complete/", views.complete_checkout_request, name="complete_checkout_request"
    ),
]
