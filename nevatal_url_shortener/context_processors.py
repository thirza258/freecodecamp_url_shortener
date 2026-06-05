from django.conf import settings


def site_settings(_request):
    return {
        "SITE_NAME": settings.SITE_NAME,
        "APP_DOMAIN": settings.APP_DOMAIN,
        "SHORT_LINK_DOMAIN": settings.SHORT_LINK_DOMAIN,
        "SHORT_LINK_PROTOCOL": settings.SHORT_LINK_PROTOCOL,
    }
