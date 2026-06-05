from __future__ import annotations


class RealIPMiddleware:
    """Normalize the client IP for trusted reverse-proxy deployments."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        forwarded = request.META.get("HTTP_X_REAL_IP", "")
        if forwarded:
            request.META["REMOTE_ADDR"] = forwarded.strip()
        return self.get_response(request)
