"""
API URL Configuration
Routes for all REST endpoints
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from .views import (
    UserRegistrationViewSet,
    UserViewSet,
    PublicationTypeViewSet,
    AuthorViewSet,
    SubjectViewSet,
    ItemViewSet,
    PublicationViewSet,
    LoanViewSet,
    HoldViewSet,
    NotificationViewSet,
    ObtainAuthTokenView,
)
from .health_check import HealthCheckView, DetailedHealthCheckView
from .analytics_views import (
    metrics_summary_view,
    performance_dashboard_view,
    sla_status_view,
    request_trends_view,
    error_trends_view,
    alerts_view,
    user_activity_view,
    library_analytics_view,
    circulation_analytics_view,
    users_analytics_view,
    system_health_view,
)

app_name = "api"

# Create router and register viewsets
router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"authors", AuthorViewSet, basename="author")
router.register(r"subjects", SubjectViewSet, basename="subject")
router.register(r"publication-types", PublicationTypeViewSet, basename="publication-type")
router.register(r"publications", PublicationViewSet, basename="publication")
router.register(r"items", ItemViewSet, basename="item")
router.register(r"loans", LoanViewSet, basename="loan")
router.register(r"holds", HoldViewSet, basename="hold")
router.register(r"notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    # API documentation
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="api:schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="api:schema"), name="redoc"),
    
    # Health checks (for monitoring)
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("health/detailed/", DetailedHealthCheckView.as_view(), name="health-check-detailed"),
    
    # Analytics and monitoring endpoints (admin only)
    path("analytics/metrics-summary/", metrics_summary_view, name="metrics-summary"),
    path("analytics/performance/", performance_dashboard_view, name="performance-dashboard"),
    path("analytics/sla-status/", sla_status_view, name="sla-status"),
    path("analytics/trends/requests/", request_trends_view, name="request-trends"),
    path("analytics/trends/errors/", error_trends_view, name="error-trends"),
    path("analytics/alerts/", alerts_view, name="alerts"),
    path("analytics/user-activity/", user_activity_view, name="user-activity"),
    path("analytics/library/", library_analytics_view, name="library-analytics"),
    path("analytics/circulation/", circulation_analytics_view, name="circulation-analytics"),
    path("analytics/users/", users_analytics_view, name="users-analytics"),
    path("analytics/system-health/", system_health_view, name="system-health"),
    
    # Authentication
    path("auth/register/", UserRegistrationViewSet.as_view({"post": "create"}), name="register"),
    path("auth/token/", ObtainAuthTokenView.as_view(), name="token_obtain"),
    
    # Router URLs
    path("", include(router.urls)),
]
