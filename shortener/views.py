from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import F, Sum
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django_ratelimit.decorators import ratelimit

from .forms import ShortURLForm
from .models import ClickEvent, ShortURL
from .rate_limits import create_rate, redirect_rate
from .utils import build_qr_data_uri, build_short_link


def _ratelimited_response(request: HttpRequest) -> HttpResponse | None:
    if getattr(request, "limited", False):
        return render(request, "429.html", status=429)
    return None


@ratelimit(key="ip", rate=create_rate, method="POST", block=False)
def index(request: HttpRequest) -> HttpResponse:
    limited_response = _ratelimited_response(request)
    if limited_response is not None:
        return limited_response

    form = ShortURLForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            short_url = ShortURL.objects.create_short_url(
                original_url=form.cleaned_data["original_url"],
                short_code=form.cleaned_data["short_code"] or None,
            )
        except ValidationError as exc:
            if hasattr(exc, "message_dict"):
                for field, messages in exc.message_dict.items():
                    for message in messages:
                        form.add_error(field if field != "__all__" else None, message)
            else:
                for message in exc.messages:
                    form.add_error(None, message)
        except IntegrityError:
            form.add_error("short_code", "This short URL already exists. Please choose another slug.")
        else:
            return redirect("success", short_code=short_url.short_code)

    total_clicks = ShortURL.objects.aggregate(total=Sum("click_count"))["total"]
    total_links = ShortURL.objects.count()
    top_urls = ShortURL.objects.filter(is_active=True).order_by("-click_count", "-created_at")[:5]
    recent_urls = ShortURL.objects.order_by("-created_at")[:10]
    return render(
        request,
        "shortener/index.html",
        {
            "form": form,
            "total_links": total_links,
            "total_clicks": total_clicks or 0,
            "top_urls": top_urls,
            "recent_urls": recent_urls,
        },
    )


def success(request: HttpRequest, short_code: str) -> HttpResponse:
    short_url = get_object_or_404(ShortURL, short_code=short_code)
    short_link = build_short_link(short_url.short_code)
    return render(
        request,
        "shortener/success.html",
        {
            "short_url": short_url,
            "short_link": short_link,
            "qr_code_data_uri": build_qr_data_uri(short_link),
        },
    )


def dashboard(request: HttpRequest) -> HttpResponse:
    total_links = ShortURL.objects.count()
    total_clicks = ShortURL.objects.aggregate(total=Sum("click_count"))["total"] or 0
    active_links = ShortURL.objects.filter(is_active=True).count()
    inactive_links = total_links - active_links
    recent_activity = ClickEvent.objects.select_related("short_url").order_by("-timestamp")[:12]
    top_urls = ShortURL.objects.order_by("-click_count", "-created_at")[:10]
    return render(
        request,
        "shortener/dashboard.html",
        {
            "total_links": total_links,
            "total_clicks": total_clicks,
            "active_links": active_links,
            "inactive_links": inactive_links,
            "recent_activity": recent_activity,
            "top_urls": top_urls,
        },
    )


@ratelimit(key="ip", rate=redirect_rate, method="GET", block=False)
def redirect_short_code(request: HttpRequest, short_code: str) -> HttpResponse:
    limited_response = _ratelimited_response(request)
    if limited_response is not None:
        return limited_response

    short_url = get_object_or_404(ShortURL, short_code=short_code, is_active=True)
    now = timezone.now()
    ShortURL.objects.filter(pk=short_url.pk).update(click_count=F("click_count") + 1, last_accessed_at=now)
    ClickEvent.objects.create(
        short_url=short_url,
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        referer=request.META.get("HTTP_REFERER", ""),
        ip_address=request.META.get("REMOTE_ADDR") or None,
    )
    return redirect(short_url.original_url, permanent=False)


def health_check(_request: HttpRequest) -> HttpResponse:
    return HttpResponse("ok", content_type="text/plain")


def not_found(request: HttpRequest, exception: Exception | None = None) -> HttpResponse:
    if isinstance(exception, Http404) or exception is None:
        return render(request, "404.html", status=404)
    return render(request, "404.html", status=404)


def server_error(request: HttpRequest) -> HttpResponse:
    return render(request, "500.html", status=500)
