import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.tests.factories import UserFactory


@pytest.mark.django_db
class TestAdminAreaCBV:
    """Covers RoleRequiredMixin via AdminAreaView."""

    def test_admin_can_access(self, client):
        admin = UserFactory(username="admin1", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)

        response = client.get(reverse("dashboard:admin_area"))

        assert response.status_code == 200

    def test_student_is_forbidden(self, client):
        student = UserFactory(username="student1", password="pass12345", role=User.Role.STUDENT)
        client.force_login(student)

        response = client.get(reverse("dashboard:admin_area"))

        assert response.status_code == 403

    def test_anonymous_user_is_redirected_to_login(self, client):
        response = client.get(reverse("dashboard:admin_area"))

        assert response.status_code == 302
        assert reverse("accounts:login") in response.url


@pytest.mark.django_db
class TestReportsPreviewFBV:
    """Covers the role_required decorator via reports_preview, including
    the multiple-allowed-roles case (ADMIN and STAFF both permitted)."""

    def test_admin_can_access(self, client):
        admin = UserFactory(username="admin2", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)

        response = client.get(reverse("dashboard:reports_preview"))

        assert response.status_code == 200

    def test_staff_can_access(self, client):
        staff = UserFactory(username="staff1", password="pass12345", role=User.Role.STAFF)
        client.force_login(staff)

        response = client.get(reverse("dashboard:reports_preview"))

        assert response.status_code == 200

    def test_teacher_is_forbidden(self, client):
        teacher = UserFactory(username="teacher1", password="pass12345", role=User.Role.TEACHER)
        client.force_login(teacher)

        response = client.get(reverse("dashboard:reports_preview"))

        assert response.status_code == 403