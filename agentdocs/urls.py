from django.urls import path

from . import views

urlpatterns = [
    path(".well-known/<path:doc_path>", views.well_known, name="agent-well-known"),
    path("auth.md", views.auth_md, name="auth-md"),
    path("llms.txt", views.llms_txt, name="llms-txt"),
]
