from django.conf import settings


def feature_flags(request):
    """Expose runtime feature flags to templates.

    Returns a small dict of flags that can be used in templates to gate UI features.
    """
    return {
        'BARCODE_ENABLED': getattr(settings, 'BARCODE_ENABLED', False),
    }
