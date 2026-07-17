import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.tests.factories import UserFactory
from apps.staff.tests.factories import StaffFactory


@pytest.mark.django_db
class TestStaffListView:
    def test_admin_can_view_list(self, client):
        admin = UserFactory(username="admin_s1", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)

        response = client.get(reverse("staff:list"))

        assert response.status_code == 200

    def test_staff_can_view_list(self, client):
        staff = StaffFactory()
        client.force_login(staff.user)

        response = client.get(reverse("staff:list"))

        assert response.status_code == 200

    def test_teacher_is_forbidden(self, client):
        """
        Deliberate divergence from Teacher's own CAN_VIEW_TEACHERS (which
        DOES admit Teacher) - see permissions.py for why.
        """
        teacher_user = UserFactory(
            username="teacher_s1", password="pass12345", role=User.Role.TEACHER
        )
        client.force_login(teacher_user)

        response = client.get(reverse("staff:list"))

        assert response.status_code == 403


@pytest.mark.django_db
class TestStaffCreateView:
    def test_admin_can_create_staff(self, client):
        admin = UserFactory(username="admin_s2", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)

        response = client.post(
            reverse("staff:create"),
            {
                "first_name": "Margaret",
                "last_name": "Hamilton",
                "email": "margaret.hamilton@example.com",
                "employee_id": "STF00999",
                "job_title": "Systems Administrator",
                "employment_type": "FULL_TIME",
                "date_of_birth": "1978-08-17",
                "date_joined": "2016-05-01",
                "phone_number": "",
                "address": "",
            },
        )

        assert response.status_code == 302
        assert User.objects.filter(username="STF00999", role=User.Role.STAFF).exists()

    def test_regular_staff_member_cannot_create_another_staff_member(self, client):
        """
        The key policy divergence from Teacher: CAN_MANAGE_STAFF is
        ADMIN-only, unlike CAN_MANAGE_TEACHERS which includes STAFF.
        """
        staff = StaffFactory()
        client.force_login(staff.user)

        response = client.get(reverse("staff:create"))

        assert response.status_code == 403


@pytest.mark.django_db
class TestStaffUpdateObjectLevelPermission:
    def test_staff_member_can_edit_their_own_profile(self, client):
        staff = StaffFactory()
        client.force_login(staff.user)

        response = client.post(
            reverse("staff:update", args=[staff.pk]),
            {
                "job_title": "Senior Librarian",
                "employment_type": "FULL_TIME",
                "phone_number": "",
                "address": "",
            },
        )

        staff.refresh_from_db()
        assert response.status_code == 302
        assert staff.job_title == "Senior Librarian"

    def test_staff_member_cannot_edit_a_colleagues_profile(self, client):
        """
        This is the case that would slip through if CAN_MANAGE_STAFF
        included STAFF the way Teacher's does - proves the stricter
        policy choice actually holds.
        """
        staff = StaffFactory()
        colleague = StaffFactory()
        client.force_login(staff.user)

        response = client.get(reverse("staff:update", args=[colleague.pk]))

        assert response.status_code == 403

    def test_admin_can_edit_any_staff_profile(self, client):
        admin = UserFactory(username="admin_s3", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        staff = StaffFactory()

        response = client.post(
            reverse("staff:update", args=[staff.pk]),
            {
                "job_title": "Admin Updated",
                "employment_type": "FULL_TIME",
                "phone_number": "",
                "address": "",
            },
        )

        staff.refresh_from_db()
        assert response.status_code == 302
        assert staff.job_title == "Admin Updated"


@pytest.mark.django_db
class TestStaffDeactivateView:
    def test_admin_can_deactivate(self, client):
        admin = UserFactory(username="admin_s4", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        staff = StaffFactory()

        response = client.post(reverse("staff:deactivate", args=[staff.pk]))

        staff.refresh_from_db()
        assert response.status_code == 302
        assert staff.is_active is False

    def test_staff_cannot_deactivate_even_themselves(self, client):
        staff = StaffFactory()
        client.force_login(staff.user)

        response = client.post(reverse("staff:deactivate", args=[staff.pk]))

        assert response.status_code == 403