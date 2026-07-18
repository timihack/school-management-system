import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.tests.factories import UserFactory
from apps.departments.tests.factories import DepartmentFactory
from apps.teachers.tests.factories import TeacherFactory


@pytest.mark.django_db
class TestDepartmentListView:
    def test_admin_can_view_list(self, client):
        admin = UserFactory(username="admin_d1", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)

        response = client.get(reverse("departments:list"))

        assert response.status_code == 200

    def test_teacher_can_view_list(self, client):
        """CAN_VIEW_DEPARTMENTS includes Teacher, unlike CAN_VIEW_STAFF."""
        teacher = TeacherFactory()
        client.force_login(teacher.user)

        response = client.get(reverse("departments:list"))

        assert response.status_code == 200

    def test_student_role_is_forbidden(self, client):
        student = UserFactory(username="student_d1", password="pass12345", role=User.Role.STUDENT)
        client.force_login(student)

        response = client.get(reverse("departments:list"))

        assert response.status_code == 403


@pytest.mark.django_db
class TestDepartmentCreateView:
    def test_admin_can_create_department(self, client):
        admin = UserFactory(username="admin_d2", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)

        response = client.post(
            reverse("departments:create"),
            {"name": "Mathematics", "description": "The Maths department.", "head_of_department": ""},
        )

        assert response.status_code == 302
        from apps.departments.models import Department
        assert Department.objects.filter(name="Mathematics").exists()

    def test_staff_cannot_create_department(self, client):
        """
        Deliberate divergence: CAN_MANAGE_DEPARTMENTS is Admin-only,
        unlike CAN_MANAGE_TEACHERS which admits Staff.
        """
        staff = UserFactory(username="staff_d1", password="pass12345", role=User.Role.STAFF)
        client.force_login(staff)

        response = client.get(reverse("departments:create"))

        assert response.status_code == 403

    def test_head_of_department_must_be_teacher_or_staff(self, client):
        admin = UserFactory(username="admin_d3", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        student = UserFactory(username="student_d2", password="pass12345", role=User.Role.STUDENT)

        response = client.post(
            reverse("departments:create"),
            {
                "name": "Science",
                "description": "",
                "head_of_department": student.pk,
            },
        )

        # The submitted PK isn't in the restricted queryset, so
        # ModelChoiceField rejects it as an invalid choice.
        assert response.status_code == 200
        assert b"valid choice" in response.content


@pytest.mark.django_db
class TestDepartmentDeleteView:
    def test_admin_can_delete(self, client):
        admin = UserFactory(username="admin_d4", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        department = DepartmentFactory()

        response = client.post(reverse("departments:delete", args=[department.pk]))

        assert response.status_code == 302
        assert not department.__class__.objects.filter(pk=department.pk).exists()

    def test_teacher_cannot_delete(self, client):
        teacher = TeacherFactory()
        department = DepartmentFactory()
        client.force_login(teacher.user)

        response = client.post(reverse("departments:delete", args=[department.pk]))

        assert response.status_code == 403