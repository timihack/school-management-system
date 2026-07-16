import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.tests.factories import UserFactory
from apps.teachers.tests.factories import TeacherFactory


@pytest.mark.django_db
class TestTeacherListView:
    def test_admin_can_view_list(self, client):
        admin = UserFactory(username="admin_t1", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)

        response = client.get(reverse("teachers:list"))

        assert response.status_code == 200

    def test_teacher_can_view_list(self, client):
        """Teachers can see the staff directory - unlike Students/Parents lists."""
        teacher = TeacherFactory()
        client.force_login(teacher.user)

        response = client.get(reverse("teachers:list"))

        assert response.status_code == 200

    def test_student_role_is_forbidden(self, client):
        student_user = UserFactory(
            username="student_t1", password="pass12345", role=User.Role.STUDENT
        )
        client.force_login(student_user)

        response = client.get(reverse("teachers:list"))

        assert response.status_code == 403


@pytest.mark.django_db
class TestTeacherCreateView:
    def test_admin_can_create_teacher(self, client):
        admin = UserFactory(username="admin_t2", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)

        response = client.post(
            reverse("teachers:create"),
            {
                "first_name": "Alan",
                "last_name": "Turing",
                "email": "alan.turing@example.com",
                "employee_id": "EMP00999",
                "qualification": "PhD Mathematics",
                "date_of_birth": "1970-06-23",
                "date_joined": "2015-09-01",
                "phone_number": "",
                "address": "",
            },
        )

        assert response.status_code == 302
        assert User.objects.filter(username="EMP00999", role=User.Role.TEACHER).exists()

    def test_teacher_cannot_create_another_teacher(self, client):
        """Teachers can VIEW the directory but can't MANAGE it - CAN_MANAGE_TEACHERS excludes TEACHER."""
        teacher = TeacherFactory()
        client.force_login(teacher.user)

        response = client.get(reverse("teachers:create"))

        assert response.status_code == 403


@pytest.mark.django_db
class TestTeacherUpdateObjectLevelPermission:
    """
    The core of this phase: RoleRequiredMixin alone would let ANY teacher
    edit ANY other teacher's profile, since TEACHER is in allowed_roles.
    These tests prove the additional object-level check in
    _get_teacher_or_403() actually restricts a teacher to their OWN
    record.
    """

    def test_teacher_can_edit_their_own_profile(self, client):
        teacher = TeacherFactory()
        client.force_login(teacher.user)

        response = client.post(
            reverse("teachers:update", args=[teacher.pk]),
            {"qualification": "Updated Qualification", "phone_number": "", "address": ""},
        )

        teacher.refresh_from_db()
        assert response.status_code == 302
        assert teacher.qualification == "Updated Qualification"

    def test_teacher_cannot_edit_a_colleagues_profile(self, client):
        teacher = TeacherFactory()
        colleague = TeacherFactory()
        client.force_login(teacher.user)

        response = client.get(reverse("teachers:update", args=[colleague.pk]))

        assert response.status_code == 403

    def test_admin_can_edit_any_teachers_profile(self, client):
        admin = UserFactory(username="admin_t3", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        teacher = TeacherFactory()

        response = client.post(
            reverse("teachers:update", args=[teacher.pk]),
            {"qualification": "Admin Updated", "phone_number": "", "address": ""},
        )

        teacher.refresh_from_db()
        assert response.status_code == 302
        assert teacher.qualification == "Admin Updated"

    def test_staff_can_edit_any_teachers_profile(self, client):
        staff = UserFactory(username="staff_t1", password="pass12345", role=User.Role.STAFF)
        client.force_login(staff)
        teacher = TeacherFactory()

        response = client.get(reverse("teachers:update", args=[teacher.pk]))

        assert response.status_code == 200


@pytest.mark.django_db
class TestTeacherDeactivateView:
    def test_admin_can_deactivate(self, client):
        admin = UserFactory(username="admin_t4", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        teacher = TeacherFactory()

        response = client.post(reverse("teachers:deactivate", args=[teacher.pk]))

        teacher.refresh_from_db()
        assert response.status_code == 302
        assert teacher.is_active is False

    def test_teacher_cannot_deactivate_even_themselves(self, client):
        """Deactivation is Admin-only - the self-edit exception applies to profile edits only."""
        teacher = TeacherFactory()
        client.force_login(teacher.user)

        response = client.post(reverse("teachers:deactivate", args=[teacher.pk]))

        assert response.status_code == 403