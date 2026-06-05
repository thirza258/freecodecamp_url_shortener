"""WSGI config for Nevatal URL Shortener."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nevatal_url_shortener.settings")

application = get_wsgi_application()
