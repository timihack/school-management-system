import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.tests.factories import UserFactory
from apps.classes.models import ClassLevel
from apps.classes.tests.factories import ClassArmFactory, ClassLevelFactory
from apps.students.tests.factories import StudentFactory


@pytest.mark.django_db
class TestClassLevelListView:
    def test_admin_can_view(self, client):
        admin = UserFactory(username="admin_cl1", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)

        response = client.get(reverse("classes:list"))

        assert response.status_code == 200

    def test_student_is_forbidden(self, client):
        student = UserFactory(username="student_cl1", password="pass12345", role=User.Role.STUDENT)
        client.force_login(student)

        response = client.get(reverse("classes:list"))

        assert response.status_code == 403


@pytest.mark.django_db
class TestClassLevelCreateView:
    def test_admin_can_create_and_gets_a_default_policy(self, client):
        admin = UserFactory(username="admin_cl2", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)

        response = client.post(
            reverse("classes:create"),
            {
                "name": "JSS1",
                "category": "JUNIOR_SECONDARY",
                "order": 7,
                "has_arms": "on",
                "assessment_type": "SCORE_BASED",
                "promotes_to": "",
                "exit_requires_arm_placement": "",
            },
        )

        assert response.status_code == 302
        level = ClassLevel.objects.get(name="JSS1")
        assert hasattr(level, "promotion_policy")

    def test_staff_cannot_create_class_level(self, client):
        staff = UserFactory(username="staff_cl1", password="pass12345", role=User.Role.STAFF)
        client.force_login(staff)

        response = client.get(reverse("classes:create"))

        assert response.status_code == 403


@pytest.mark.django_db
class TestClassEnrollmentView:
    def test_staff_can_assign_student_to_arm(self, client):
        staff = UserFactory(username="staff_cl2", password="pass12345", role=User.Role.STAFF)
        client.force_login(staff)
        student = StudentFactory()
        arm = ClassArmFactory()

        response = client.post(
            reverse("classes:enroll_student", args=[student.pk]),
            {"class_level": arm.class_level.pk, "class_arm": arm.pk, "is_repeat": ""},
        )

        assert response.status_code == 302

    def test_arm_required_when_level_has_arms(self, client):
        staff = UserFactory(username="staff_cl3", password="pass12345", role=User.Role.STAFF)
        client.force_login(staff)
        student = StudentFactory()
        level = ClassLevelFactory(has_arms=True)

        response = client.post(
            reverse("classes:enroll_student", args=[student.pk]),
            {"class_level": level.pk, "class_arm": "", "is_repeat": ""},
        )

        assert response.status_code == 200
        assert b"requires an arm" in response.content

    def test_mismatched_arm_and_level_is_rejected(self, client):
        staff = UserFactory(username="staff_cl4", password="pass12345", role=User.Role.STAFF)
        client.force_login(staff)
        student = StudentFactory()
        level_a = ClassLevelFactory(has_arms=True)
        arm_from_other_level = ClassArmFactory()  # belongs to a DIFFERENT level

        response = client.post(
            reverse("classes:enroll_student", args=[student.pk]),
            {"class_level": level_a.pk, "class_arm": arm_from_other_level.pk, "is_repeat": ""},
        )

        assert response.status_code == 200
        assert b"does not belong" in response.content

    def test_admin_can_reassign_and_history_is_preserved(self, client):
        admin = UserFactory(username="admin_cl3", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        student = StudentFactory()
        arm_a = ClassArmFactory()
        arm_b = ClassArmFactory(class_level=arm_a.class_level)

        client.post(
            reverse("classes:enroll_student", args=[student.pk]),
            {"class_level": arm_a.class_level.pk, "class_arm": arm_a.pk, "is_repeat": ""},
        )
        client.post(
            reverse("classes:enroll_student", args=[student.pk]),
            {"class_level": arm_a.class_level.pk, "class_arm": arm_b.pk, "is_repeat": ""},
        )

        assert student.class_enrollments.count() == 2
        assert student.class_enrollments.filter(is_current=True).count() == 1