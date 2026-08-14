from django.urls import path

from . import views

app_name = "subjects"

urlpatterns = [
    path("", views.SubjectListView.as_view(), name="list"),
    path("create/", views.SubjectCreateView.as_view(), name="create"),
    path("<int:pk>/", views.SubjectDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.SubjectUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.SubjectDeleteView.as_view(), name="delete"),
    path(
        "<int:subject_pk>/components/create/",
        views.AssessmentComponentCreateView.as_view(),
        name="component_create",
    ),
    path(
        "components/<int:pk>/delete/",
        views.AssessmentComponentDeleteView.as_view(),
        name="component_delete",
    ),
    path(
        "<int:subject_pk>/skill-items/create/",
        views.SkillChecklistItemCreateView.as_view(),
        name="skill_item_create",
    ),
    path(
        "skill-items/<int:pk>/delete/",
        views.SkillChecklistItemDeleteView.as_view(),
        name="skill_item_delete",
    ),
    path(
        "grading-scale/<int:level_pk>/",
        views.GradingScaleDetailView.as_view(),
        name="grading_scale_detail",
    ),
    path(
        "grading-scale/<int:level_pk>/bands/create/",
        views.GradeBandCreateView.as_view(),
        name="grade_band_create",
    ),
    path(
        "grading-scale/bands/<int:pk>/delete/",
        views.GradeBandDeleteView.as_view(),
        name="grade_band_delete",
    ),
    path(
        "<int:subject_pk>/topics/create/",
        views.TopicCreateView.as_view(),
        name="topic_create",
    ),
    path(
        "<int:subject_pk>/topics/<int:pk>/edit/",
        views.TopicUpdateView.as_view(),
        name="topic_update",
    ),
    path(
        "topics/<int:pk>/delete/",
        views.TopicDeleteView.as_view(),
        name="topic_delete",
    ),
    path(
        "curriculum/<int:level_pk>/",
        views.CurriculumOverviewView.as_view(),
        name="curriculum_overview",
    ),
]