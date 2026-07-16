from django.urls import path

from . import views

app_name = "teachers"

urlpatterns = [
    path("", views.TeacherListView.as_view(), name="list"),
    path("create/", views.TeacherCreateView.as_view(), name="create"),
    path("<int:pk>/", views.TeacherDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.TeacherUpdateView.as_view(), name="update"),
    path("<int:pk>/deactivate/", views.TeacherDeactivateView.as_view(), name="deactivate"),
]