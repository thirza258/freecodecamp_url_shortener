"""ASGI config for Nevatal URL Shortener."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nevatal_url_shortener.settings")

application = get_asgi_application()
