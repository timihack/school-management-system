import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.tests.factories import UserFactory
from apps.classes.tests.factories import ClassLevelFactory
from apps.subjects.models import Subject
from apps.subjects.selectors import get_grade_for_percentage
from apps.subjects.tests.factories import GradeBandFactory, GradingScaleFactory, SubjectFactory


@pytest.mark.django_db
class TestSubjectListView:
    def test_admin_can_view(self, client):
        admin = UserFactory(username="admin_sub1", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)

        response = client.get(reverse("subjects:list"))

        assert response.status_code == 200

    def test_teacher_can_view(self, client):
        teacher = UserFactory(username="teacher_sub1", password="pass12345", role=User.Role.TEACHER)
        client.force_login(teacher)

        response = client.get(reverse("subjects:list"))

        assert response.status_code == 200

    def test_student_is_forbidden(self, client):
        student = UserFactory(username="student_sub1", password="pass12345", role=User.Role.STUDENT)
        client.force_login(student)

        response = client.get(reverse("subjects:list"))

        assert response.status_code == 403


@pytest.mark.django_db
class TestSubjectCreateView:
    def test_admin_can_create_subject(self, client):
        admin = UserFactory(username="admin_sub2", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        level = ClassLevelFactory()

        response = client.post(
            reverse("subjects:create"),
            {
                "name": "Mathematics",
                "code": "MTH",
                "assessment_type": "SCORE_BASED",
                "computation_method": "SUM_COMPONENTS",
                "class_levels": [level.pk],
                "is_active": "on",
            },
        )

        assert response.status_code == 302
        assert Subject.objects.filter(name="Mathematics").exists()

    def test_staff_cannot_create_subject(self, client):
        staff = UserFactory(username="staff_sub1", password="pass12345", role=User.Role.STAFF)
        client.force_login(staff)

        response = client.get(reverse("subjects:create"))

        assert response.status_code == 403


@pytest.mark.django_db
class TestAssessmentComponentCreateView:
    def test_admin_can_add_component(self, client):
        admin = UserFactory(username="admin_sub3", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        subject = SubjectFactory()

        response = client.post(
            reverse("subjects:component_create", args=[subject.pk]),
            {"name": "CA1", "component_type": "CA", "max_score": 10, "order": 0},
        )

        assert response.status_code == 302
        assert subject.assessment_components.filter(name="CA1").exists()


@pytest.mark.django_db
class TestGradeBandOverlapValidation:
    def test_admin_can_add_non_overlapping_band(self, client):
        admin = UserFactory(username="admin_sub4", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        scale = GradingScaleFactory()
        GradeBandFactory(grading_scale=scale, label="A", min_percentage=75, max_percentage=100)

        response = client.post(
            reverse("subjects:grade_band_create", args=[scale.class_level.pk]),
            {"label": "B", "description": "", "min_percentage": 60, "max_percentage": 74},
        )

        assert response.status_code == 302
        assert scale.bands.filter(label="B").exists()

    def test_overlapping_band_is_rejected(self, client):
        admin = UserFactory(username="admin_sub5", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        scale = GradingScaleFactory()
        GradeBandFactory(grading_scale=scale, label="A", min_percentage=75, max_percentage=100)

        response = client.post(
            reverse("subjects:grade_band_create", args=[scale.class_level.pk]),
            {"label": "B", "description": "", "min_percentage": 70, "max_percentage": 80},
        )

        assert response.status_code == 200
        assert b"overlaps" in response.content
        assert scale.bands.filter(label="B").exists() is False


@pytest.mark.django_db
class TestGetGradeForPercentage:
    def test_returns_matching_band(self):
        scale = GradingScaleFactory()
        GradeBandFactory(grading_scale=scale, label="A", min_percentage=75, max_percentage=100)
        GradeBandFactory(grading_scale=scale, label="B", min_percentage=60, max_percentage=74)

        band = get_grade_for_percentage(scale.class_level, 82)

        assert band.label == "A"

    def test_returns_none_when_no_scale_exists(self):
        level = ClassLevelFactory()

        band = get_grade_for_percentage(level, 82)

        assert band is None

    def test_returns_none_for_percentage_in_an_unconfigured_gap(self):
        scale = GradingScaleFactory()
        GradeBandFactory(grading_scale=scale, label="A", min_percentage=90, max_percentage=100)

        band = get_grade_for_percentage(scale.class_level, 50)

        assert band is None