from django.urls import path

from . import views

app_name = "departments"

urlpatterns = [
    path("", views.DepartmentListView.as_view(), name="list"),
    path("create/", views.DepartmentCreateView.as_view(), name="create"),
    path("<int:pk>/", views.DepartmentDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.DepartmentUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.DepartmentDeleteView.as_view(), name="delete"),
]