from django.contrib import admin
from django.urls import include, path

from shortener.views import not_found, server_error

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("shortener.urls")),
]

handler404 = not_found
handler500 = server_error

