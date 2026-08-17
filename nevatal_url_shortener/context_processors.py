from django.conf import settings


def site_settings(request):
    protocol = settings.SHORT_LINK_PROTOCOL
    app_domain = settings.APP_DOMAIN
    canonical_url = f"{protocol}://{app_domain}{request.path}"
    return {
        "SITE_NAME": settings.SITE_NAME,
        "APP_DOMAIN": app_domain,
        "SHORT_LINK_DOMAIN": settings.SHORT_LINK_DOMAIN,
        "SHORT_LINK_PROTOCOL": protocol,
        "CANONICAL_URL": canonical_url,
        "SITE_DESCRIPTION": "Fast, secure, and modern URL shortener with custom slugs, live analytics, and instant QR codes.",
    }
