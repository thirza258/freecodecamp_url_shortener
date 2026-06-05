import re

from django.conf import settings
from django.urls import path, re_path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("health/", views.health_check, name="health"),
]

reserved = "|".join(re.escape(code) for code in sorted(settings.RESERVED_SHORT_CODES))
short_code_pattern = rf"^(?P<short_code>(?!({reserved})$)[-A-Za-z0-9_]+)(?:/)?$"
success_pattern = r"^success/(?P<short_code>[-A-Za-z0-9_]+)/?$"

urlpatterns += [
    re_path(short_code_pattern, views.redirect_short_code, name="redirect-short-url"),
    re_path(success_pattern, views.success, name="success"),
]
