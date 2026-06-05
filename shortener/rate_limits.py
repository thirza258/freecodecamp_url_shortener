from __future__ import annotations

from django.conf import settings


def create_rate(_group, _request) -> str:
    return getattr(settings, "SHORTENER_CREATE_RATE_LIMIT", "10/m")


def redirect_rate(_group, _request) -> str:
    return getattr(settings, "SHORTENER_REDIRECT_RATE_LIMIT", "100/m")
