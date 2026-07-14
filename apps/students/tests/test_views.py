import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.tests.factories import UserFactory
from apps.students.tests.factories import StudentFactory


@pytest.mark.django_db
class TestStudentListView:
    def test_admin_can_view_list(self, client):
        admin = UserFactory(username="admin_x", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)

        response = client.get(reverse("students:list"))

        assert response.status_code == 200

    def test_student_role_is_forbidden(self, client):
        student_user = UserFactory(
            username="student_x", password="pass12345", role=User.Role.STUDENT
        )
        client.force_login(student_user)

        response = client.get(reverse("students:list"))

        assert response.status_code == 403

    def test_search_filters_results(self, client):
        admin = UserFactory(username="admin_y", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        StudentFactory(admission_number="ADM00001")
        StudentFactory(admission_number="ADM00002")

        response = client.get(reverse("students:list"), {"search": "ADM00001"})

        assert response.status_code == 200
        assert b"ADM00001" in response.content
        assert b"ADM00002" not in response.content


@pytest.mark.django_db
class TestStudentCreateView:
    def test_admin_can_create_student(self, client):
        admin = UserFactory(username="admin_z", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)

        response = client.post(
            reverse("students:create"),
            {
                "first_name": "Katherine",
                "last_name": "Johnson",
                "email": "katherine@example.com",
                "admission_number": "ADM00999",
                "date_of_birth": "2011-03-15",
                "gender": "FEMALE",
                "admission_date": "2024-01-10",
                "address": "",
                "phone_number": "",
            },
        )

        assert response.status_code == 302
        assert User.objects.filter(username="ADM00999", role=User.Role.STUDENT).exists()

    def test_teacher_cannot_create_student(self, client):
        teacher = UserFactory(username="teacher_a", password="pass12345", role=User.Role.TEACHER)
        client.force_login(teacher)

        response = client.get(reverse("students:create"))

        assert response.status_code == 403

    def test_duplicate_admission_number_is_rejected(self, client):
        admin = UserFactory(username="admin_dup", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        StudentFactory(admission_number="ADM00111")

        response = client.post(
            reverse("students:create"),
            {
                "first_name": "Dup",
                "last_name": "Licate",
                "email": "dup@example.com",
                "admission_number": "ADM00111",
                "date_of_birth": "2011-03-15",
                "gender": "MALE",
                "admission_date": "2024-01-10",
                "address": "",
                "phone_number": "",
            },
        )

        assert response.status_code == 200
        assert b"already in use" in response.content


@pytest.mark.django_db
class TestStudentDeactivateView:
    def test_admin_can_deactivate(self, client):
        admin = UserFactory(username="admin_w", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        student = StudentFactory()

        response = client.post(reverse("students:deactivate", args=[student.pk]))

        student.refresh_from_db()
        assert response.status_code == 302
        assert student.is_active is False

    def test_staff_cannot_deactivate(self, client):
        staff = UserFactory(username="staff_w", password="pass12345", role=User.Role.STAFF)
        client.force_login(staff)
        student = StudentFactory()

        response = client.post(reverse("students:deactivate", args=[student.pk]))

        assert response.status_code == 403