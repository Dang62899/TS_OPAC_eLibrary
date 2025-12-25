"""
API URL Configuration
Routes for all REST endpoints
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
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
    
    # Authentication
    path("auth/register/", UserRegistrationViewSet.as_view({"post": "create"}), name="register"),
    path("auth/token/", obtain_auth_token, name="token_obtain"),
    
    # Router URLs
    path("", include(router.urls)),
]
