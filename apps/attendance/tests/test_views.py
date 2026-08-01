import datetime

import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.tests.factories import UserFactory
from apps.classes.tests.factories import ClassArmFactory, ClassLevelFactory
from apps.terms.services import activate_term
from apps.terms.tests.factories import TermFactory
from apps.teachers.tests.factories import TeacherFactory


@pytest.mark.django_db
class TestAttendanceRegisterAccess:
    def test_admin_can_view_the_register_page(self, client):
        admin = UserFactory(username="admin_att1", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)

        response = client.get(reverse("attendance:register"))

        assert response.status_code == 200

    def test_student_is_forbidden(self, client):
        student = UserFactory(username="student_att1", password="pass12345", role=User.Role.STUDENT)
        client.force_login(student)

        response = client.get(reverse("attendance:register"))

        assert response.status_code == 403


@pytest.mark.django_db
class TestAttendanceMarkingOwnershipArmBased:
    """
    Admin/Staff can mark ANY arm; a Teacher only the arm(s) they are
    personally the class_teacher of.
    """

    def test_teacher_can_mark_their_own_arm(self, client):
        teacher = TeacherFactory()
        arm = ClassArmFactory(class_teacher=teacher)
        client.force_login(teacher.user)

        response = client.get(
            reverse("attendance:register"),
            {"class_level": arm.class_level.pk, "class_arm": arm.pk},
        )

        assert response.status_code == 200

    def test_teacher_cannot_mark_a_colleagues_arm(self, client):
        teacher = TeacherFactory()
        colleague = TeacherFactory()
        arm = ClassArmFactory(class_teacher=colleague)
        client.force_login(teacher.user)

        response = client.get(
            reverse("attendance:register"),
            {"class_level": arm.class_level.pk, "class_arm": arm.pk},
        )

        assert response.status_code == 403

    def test_admin_can_mark_any_arm(self, client):
        admin = UserFactory(username="admin_att2", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        teacher = TeacherFactory()
        arm = ClassArmFactory(class_teacher=teacher)

        response = client.get(
            reverse("attendance:register"),
            {"class_level": arm.class_level.pk, "class_arm": arm.pk},
        )

        assert response.status_code == 200


@pytest.mark.django_db
class TestAttendanceMarkingOwnershipNoArmLevel:
    """
    The scenario this whole fix is about: a ClassLevel with
    has_arms=False has no ClassArm at all - ownership must fall back to
    the LEVEL's own class_teacher instead.
    """

    def test_level_owning_teacher_can_mark_their_no_arm_level(self, client):
        teacher = TeacherFactory()
        level = ClassLevelFactory(has_arms=False, class_teacher=teacher)
        client.force_login(teacher.user)

        response = client.get(reverse("attendance:register"), {"class_level": level.pk})

        assert response.status_code == 200

    def test_a_different_teacher_cannot_mark_someone_elses_no_arm_level(self, client):
        teacher = TeacherFactory()
        owning_teacher = TeacherFactory()
        level = ClassLevelFactory(has_arms=False, class_teacher=owning_teacher)
        client.force_login(teacher.user)

        response = client.get(reverse("attendance:register"), {"class_level": level.pk})

        assert response.status_code == 403

    def test_arm_based_level_shows_a_prompt_to_select_an_arm_rather_than_a_roster(self, client):
        admin = UserFactory(username="admin_att3", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        level = ClassLevelFactory(has_arms=True)

        response = client.get(reverse("attendance:register"), {"class_level": level.pk})

        assert response.status_code == 200
        assert b"select one to continue" in response.content


@pytest.mark.django_db
class TestAttendanceSubmission:
    def test_arm_based_submission_saves_records_and_redirects(self, client):
        teacher = TeacherFactory()
        arm = ClassArmFactory(class_teacher=teacher)
        term = TermFactory(
            start_date=datetime.date(2024, 9, 1), end_date=datetime.date(2024, 12, 15)
        )
        activate_term(term)
        client.force_login(teacher.user)

        response = client.post(
            reverse("attendance:register"),
            {"class_level": arm.class_level.pk, "class_arm": arm.pk, "date": "2024-09-10"},
        )

        assert response.status_code == 302

    def test_no_arm_level_submission_saves_records_and_redirects(self, client):
        teacher = TeacherFactory()
        level = ClassLevelFactory(has_arms=False, class_teacher=teacher)
        term = TermFactory(
            start_date=datetime.date(2024, 9, 1), end_date=datetime.date(2024, 12, 15)
        )
        activate_term(term)
        client.force_login(teacher.user)

        response = client.post(
            reverse("attendance:register"),
            {"class_level": level.pk, "date": "2024-09-10"},
        )

        assert response.status_code == 302

    def test_submitting_an_arm_based_level_without_an_arm_is_rejected_gracefully(self, client):
        admin = UserFactory(username="admin_att4", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        level = ClassLevelFactory(has_arms=True)
        term = TermFactory(
            start_date=datetime.date(2024, 9, 1), end_date=datetime.date(2024, 12, 15)
        )
        activate_term(term)

        response = client.post(
            reverse("attendance:register"),
            {"class_level": level.pk, "date": "2024-09-10"},
        )

        assert response.status_code == 302  # redirects back with an error message, doesn't 500

    def test_submission_without_a_current_term_is_rejected_gracefully(self, client):
        teacher = TeacherFactory()
        level = ClassLevelFactory(has_arms=False, class_teacher=teacher)
        client.force_login(teacher.user)

        response = client.post(
            reverse("attendance:register"),
            {"class_level": level.pk, "date": "2024-09-10"},
        )

        assert response.status_code == 302  # redirects back with an error message, doesn't 500

    def test_date_outside_the_active_terms_range_is_rejected_gracefully(self, client):
        """
        Regression test: mark_attendance's date-within-term validation
        raises ValidationError, which the view previously didn't catch
        at all - a submission for a date outside the current term's
        range 500'd instead of showing a clean error message, unlike
        every other error path in this view.
        """
        teacher = TeacherFactory()
        level = ClassLevelFactory(has_arms=False, class_teacher=teacher)
        term = TermFactory(
            start_date=datetime.date(2026, 8, 3), end_date=datetime.date(2026, 11, 27)
        )
        activate_term(term)
        client.force_login(teacher.user)

        response = client.post(
            reverse("attendance:register"),
            {"class_level": level.pk, "date": "2026-07-27"},  # before term.start_date
        )

        assert response.status_code == 302
        assert response.url == reverse("attendance:register")