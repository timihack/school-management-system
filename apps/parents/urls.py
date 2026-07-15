from django.urls import path

from . import views

app_name = "parents"

urlpatterns = [
    path("", views.ParentListView.as_view(), name="list"),
    path("create/", views.ParentCreateView.as_view(), name="create"),
    path("<int:pk>/", views.ParentDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.ParentUpdateView.as_view(), name="update"),
    path("<int:pk>/deactivate/", views.ParentDeactivateView.as_view(), name="deactivate"),
    path(
        "<int:parent_pk>/link-child/",
        views.GuardianshipCreateView.as_view(),
        name="link_child",
    ),
    path(
        "guardianship/<int:pk>/unlink/",
        views.GuardianshipDeleteView.as_view(),
        name="unlink_child",
    ),
]