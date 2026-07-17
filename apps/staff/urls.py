from django.urls import path

from . import views

app_name = "staff"

urlpatterns = [
    path("", views.StaffListView.as_view(), name="list"),
    path("create/", views.StaffCreateView.as_view(), name="create"),
    path("<int:pk>/", views.StaffDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.StaffUpdateView.as_view(), name="update"),
    path("<int:pk>/deactivate/", views.StaffDeactivateView.as_view(), name="deactivate"),
]