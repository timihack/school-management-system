import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.tests.factories import UserFactory
from apps.parents.tests.factories import GuardianshipFactory


@pytest.mark.django_db
class TestParentDashboard:
    def test_parent_sees_only_their_own_children(self, client):
        guardianship_a = GuardianshipFactory()
        guardianship_b = GuardianshipFactory()

        client.force_login(guardianship_a.parent.user)
        response = client.get(reverse("dashboard:home"))

        assert response.status_code == 200
        assert guardianship_a.student.admission_number.encode() in response.content
        assert guardianship_b.student.admission_number.encode() not in response.content

    def test_parent_without_profile_sees_friendly_message(self, client):
        parent_user = UserFactory(
            username="orphan_parent", password="pass12345", role=User.Role.PARENT
        )
        client.force_login(parent_user)

        response = client.get(reverse("dashboard:home"))

        assert response.status_code == 200
        assert b"contact the school office" in response.content

    def test_non_parent_roles_see_the_generic_dashboard(self, client):
        admin = UserFactory(username="admin_dash", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)

        response = client.get(reverse("dashboard:home"))

        assert response.status_code == 200
        assert b"Foundation is live" in response.content

    def test_child_attendance_summary_shows_correct_numbers(self, client):
        from apps.attendance.services import mark_attendance
        from apps.classes.services import assign_student_to_class
        from apps.classes.tests.factories import ClassArmFactory
        from apps.terms.services import activate_term
        from apps.terms.tests.factories import TermFactory

        guardianship = GuardianshipFactory()
        term = TermFactory(total_school_days=100)
        activate_term(term)
        arm = ClassArmFactory()
        assign_student_to_class(
            student=guardianship.student, class_level=arm.class_level, class_arm=arm
        )
        mark_attendance(
            class_level=arm.class_level,
            class_arm=arm,
            date=term.start_date,
            term=term,
            marked_by=None,
            attendance_data={guardianship.student.pk: "ABSENT"},
        )

        client.force_login(guardianship.parent.user)
        response = client.get(reverse("dashboard:home"))

        assert response.status_code == 200
        assert b"1 day absent" in response.content
        assert b"out of 100 school days" in response.content