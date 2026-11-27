"""
URL configuration for elibrary project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse


def well_known_handler(request, path):
    """Handle .well-known requests silently (browser/extension checks)"""
    return HttpResponse(status=404)


def protected_attachment_media_handler(request, path):
    """Prevent direct access to attachments outside their authorized views."""
    return HttpResponse(status=404)


SERVICE_WORKER_JS = """
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', () => {});
"""


def service_worker(request):
    """Root-scoped service worker so the app is installable; it never caches pages."""
    return HttpResponse(SERVICE_WORKER_JS, content_type="application/javascript")


urlpatterns = [
    path("sw.js", service_worker),
    path("admin/", admin.site.urls),  # Only accessible to superusers
    path("api/v1/", include("api.urls")),  # REST API endpoints
    path("media/attachments/<path:path>", protected_attachment_media_handler),
    path("", include("catalog.urls")),
    path("circulation/", include("circulation.urls")),
    path("accounts/", include("accounts.urls")),
    path(".well-known/<path:path>", well_known_handler),  # Suppress .well-known warnings
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
