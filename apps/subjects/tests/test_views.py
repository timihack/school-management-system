import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.tests.factories import UserFactory
from apps.classes.tests.factories import ClassLevelFactory
from apps.subjects.models import Subject, Topic
from apps.subjects.selectors import get_grade_for_percentage
from apps.subjects.tests.factories import (
    GradeBandFactory,
    GradingScaleFactory,
    SubjectFactory,
    TopicFactory,
)


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


@pytest.mark.django_db
class TestTopicCreateView:
    def test_admin_can_create_topic(self, client):
        admin = UserFactory(username="admin_topic1", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        subject = SubjectFactory()
        level = ClassLevelFactory()
        subject.class_levels.add(level)

        response = client.post(
            reverse("subjects:topic_create", args=[subject.pk]),
            {"class_level": level.pk, "term": "", "name": "Fractions", "description": "", "order": 0},
        )

        assert response.status_code == 302
        assert Topic.objects.filter(subject=subject, name="Fractions").exists()

    def test_staff_can_create_topic(self, client):
        """
        Confirms Curriculum management is genuinely BROADER than
        Subject management (test_staff_cannot_create_subject above is
        the direct contrast - Staff is blocked from Subject, but
        allowed here).
        """
        staff = UserFactory(username="staff_topic1", password="pass12345", role=User.Role.STAFF)
        client.force_login(staff)
        subject = SubjectFactory()
        level = ClassLevelFactory()
        subject.class_levels.add(level)

        response = client.post(
            reverse("subjects:topic_create", args=[subject.pk]),
            {"class_level": level.pk, "term": "", "name": "Fractions", "description": "", "order": 0},
        )

        assert response.status_code == 302
        assert Topic.objects.filter(subject=subject, name="Fractions").exists()

    def test_teacher_can_create_topic(self, client):
        teacher = UserFactory(username="teacher_topic1", password="pass12345", role=User.Role.TEACHER)
        client.force_login(teacher)
        subject = SubjectFactory()
        level = ClassLevelFactory()
        subject.class_levels.add(level)

        response = client.post(
            reverse("subjects:topic_create", args=[subject.pk]),
            {"class_level": level.pk, "term": "", "name": "Fractions", "description": "", "order": 0},
        )

        assert response.status_code == 302
        assert Topic.objects.filter(subject=subject, name="Fractions").exists()

    def test_student_is_forbidden(self, client):
        student = UserFactory(username="student_topic1", password="pass12345", role=User.Role.STUDENT)
        client.force_login(student)
        subject = SubjectFactory()

        response = client.get(reverse("subjects:topic_create", args=[subject.pk]))

        assert response.status_code == 403


@pytest.mark.django_db
class TestTopicClassLevelScoping:
    """
    Confirms TopicForm's class_level queryset is genuinely scoped to
    the subject's assigned class_levels, not every ClassLevel in the
    system - same test-what-you-claim discipline as
    TestGradeBandOverlapValidation above.
    """

    def test_class_level_not_assigned_to_subject_is_rejected(self, client):
        admin = UserFactory(username="admin_topic2", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        subject = SubjectFactory()
        unrelated_level = ClassLevelFactory()  # deliberately NOT added to subject.class_levels

        response = client.post(
            reverse("subjects:topic_create", args=[subject.pk]),
            {
                "class_level": unrelated_level.pk,
                "term": "",
                "name": "Fractions",
                "description": "",
                "order": 0,
            },
        )

        assert response.status_code == 200  # form re-rendered with a validation error
        assert not Topic.objects.filter(subject=subject, name="Fractions").exists()


@pytest.mark.django_db
class TestTopicDeleteView:
    def test_teacher_can_delete_topic(self, client):
        teacher = UserFactory(username="teacher_topic2", password="pass12345", role=User.Role.TEACHER)
        client.force_login(teacher)
        topic = TopicFactory()

        response = client.post(reverse("subjects:topic_delete", args=[topic.pk]))

        assert response.status_code == 302
        assert not Topic.objects.filter(pk=topic.pk).exists()

    def test_student_cannot_delete_topic(self, client):
        student = UserFactory(username="student_topic2", password="pass12345", role=User.Role.STUDENT)
        client.force_login(student)
        topic = TopicFactory()

        response = client.post(reverse("subjects:topic_delete", args=[topic.pk]))

        assert response.status_code == 403
        assert Topic.objects.filter(pk=topic.pk).exists()


@pytest.mark.django_db
class TestCurriculumOverviewView:
    def test_teacher_can_view_curriculum_overview(self, client):
        teacher = UserFactory(username="teacher_topic3", password="pass12345", role=User.Role.TEACHER)
        client.force_login(teacher)
        topic = TopicFactory()

        response = client.get(reverse("subjects:curriculum_overview", args=[topic.class_level.pk]))

        assert response.status_code == 200
        assert topic.subject in response.context["grouped_topics"]

    def test_student_is_forbidden(self, client):
        student = UserFactory(username="student_topic3", password="pass12345", role=User.Role.STUDENT)
        client.force_login(student)
        level = ClassLevelFactory()

        response = client.get(reverse("subjects:curriculum_overview", args=[level.pk]))

        assert response.status_code == 403