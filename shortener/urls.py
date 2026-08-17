import re

from django.conf import settings
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path, re_path

from .forms import LoginForm
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("register/", views.register, name="register"),
    path(
        "login/",
        LoginView.as_view(template_name="registration/login.html", authentication_form=LoginForm),
        name="login",
    ),
    path("logout/", LogoutView.as_view(next_page="index"), name="logout"),
    path("health/", views.health_check, name="health"),
    path("robots.txt", views.robots_txt, name="robots_txt"),
    path("sitemap.xml", views.sitemap_xml, name="sitemap_xml"),
    path("site.webmanifest", views.site_manifest, name="site_manifest"),
    path("manifest.json", views.site_manifest, name="manifest_json"),
]

reserved = "|".join(re.escape(code) for code in sorted(settings.RESERVED_SHORT_CODES))
short_code_pattern = rf"^(?P<short_code>(?!({reserved})$)[-A-Za-z0-9_]+)(?:/)?$"
success_pattern = r"^success/(?P<short_code>[-A-Za-z0-9_]+)/?$"

urlpatterns += [
    re_path(short_code_pattern, views.redirect_short_code, name="redirect-short-url"),
    re_path(success_pattern, views.success, name="success"),
]
