from __future__ import annotations

from django.conf import settings


class RealIPMiddleware:
    """Normalize the client IP for trusted reverse-proxy deployments."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        forwarded = request.META.get("HTTP_X_REAL_IP", "")
        if forwarded:
            request.META["REMOTE_ADDR"] = forwarded.strip()
        return self.get_response(request)


class FrameAncestorsMiddleware:
    """Emit a CSP ``frame-ancestors`` policy so the site can be embedded.

    Replaces Django's ``XFrameOptionsMiddleware``: the X-Frame-Options header
    cannot express a list of allowed embedders, and its ``DENY`` value blocked
    iframe embedding entirely. The ``FRAME_ANCESTORS`` env var (comma-separated
    origins, ``*`` for any origin, ``none`` to block all) controls who may
    embed the site.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        ancestors = getattr(settings, "X_FRAME_ANCESTORS", ())
        if ancestors:
            sources = " ".join("'none'" if item == "none" else item for item in ancestors)
            policy = f"frame-ancestors {sources};"
            existing = response.get("Content-Security-Policy")
            response["Content-Security-Policy"] = f"{existing} {policy}".strip() if existing else policy
        return response
