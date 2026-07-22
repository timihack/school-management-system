from django.urls import path

from . import views

app_name = "terms"

urlpatterns = [
    path("", views.AcademicSessionListView.as_view(), name="session_list"),
    path("create/", views.AcademicSessionCreateView.as_view(), name="session_create"),
    path("<int:pk>/", views.AcademicSessionDetailView.as_view(), name="session_detail"),
    path("<int:pk>/edit/", views.AcademicSessionUpdateView.as_view(), name="session_update"),
    path("<int:pk>/delete/", views.AcademicSessionDeleteView.as_view(), name="session_delete"),
    path(
        "<int:session_pk>/terms/create/", views.TermCreateView.as_view(), name="term_create"
    ),
    path("terms/<int:pk>/edit/", views.TermUpdateView.as_view(), name="term_update"),
    path("terms/<int:pk>/delete/", views.TermDeleteView.as_view(), name="term_delete"),
    path("terms/<int:pk>/activate/", views.TermActivateView.as_view(), name="term_activate"),
]