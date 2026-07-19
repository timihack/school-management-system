from django.urls import path

from . import views

app_name = "classes"

urlpatterns = [
    path("", views.ClassLevelListView.as_view(), name="list"),
    path("create/", views.ClassLevelCreateView.as_view(), name="create"),
    path("<int:pk>/", views.ClassLevelDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.ClassLevelUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.ClassLevelDeleteView.as_view(), name="delete"),
    path("<int:level_pk>/arms/create/", views.ClassArmCreateView.as_view(), name="arm_create"),
    path("arms/<int:pk>/edit/", views.ClassArmUpdateView.as_view(), name="arm_update"),
    path("arms/<int:pk>/delete/", views.ClassArmDeleteView.as_view(), name="arm_delete"),
    path(
        "<int:level_pk>/policy/",
        views.PromotionPolicyUpdateView.as_view(),
        name="policy_update",
    ),
    path(
        "enroll/<int:student_pk>/",
        views.ClassEnrollmentCreateView.as_view(),
        name="enroll_student",
    ),
]