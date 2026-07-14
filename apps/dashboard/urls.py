from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("admin-area/", views.AdminAreaView.as_view(), name="admin_area"),
    path("reports-preview/", views.reports_preview, name="reports_preview"),
]