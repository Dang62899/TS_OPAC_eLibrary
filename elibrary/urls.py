"""
URL configuration for elibrary project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse

# Only allow superusers to access admin


def superuser_required(view_func):
    decorated_view_func = user_passes_test(lambda u: u.is_superuser)(view_func)
    return decorated_view_func


# Wrap admin.site.urls with superuser check
admin.site.login = superuser_required(admin.site.login)


def well_known_handler(request, path):
    """Handle .well-known requests silently (browser/extension checks)"""
    return HttpResponse(status=404)


urlpatterns = [
    path("admin/", admin.site.urls),  # Only accessible to superusers
    path("", include("catalog.urls")),
    path("circulation/", include("circulation.urls")),
    path("accounts/", include("accounts.urls")),
    path(".well-known/<path:path>", well_known_handler),  # Suppress .well-known warnings
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
