import datetime

import pytest

from apps.accounts.models import User
from apps.teachers.services import TeacherCreateData, create_teacher, deactivate_teacher
from apps.teachers.tests.factories import TeacherFactory


@pytest.mark.django_db
class TestCreateTeacher:
    def test_creates_linked_user_and_teacher(self):
        data = TeacherCreateData(
            first_name="Rosalind",
            last_name="Franklin",
            email="rosalind.franklin@example.com",
            employee_id="EMP00123",
            date_of_birth=datetime.date(1980, 7, 25),
            date_joined=datetime.date(2020, 1, 10),
            qualification="PhD Chemistry",
        )

        teacher, temporary_password = create_teacher(data)

        assert teacher.pk is not None
        assert teacher.user.role == User.Role.TEACHER
        assert teacher.user.check_password(temporary_password)
        assert teacher.user.username == "EMP00123"


@pytest.mark.django_db
class TestDeactivateTeacher:
    def test_deactivates_teacher_and_disables_login(self):
        teacher = TeacherFactory()

        deactivate_teacher(teacher)
        teacher.refresh_from_db()
        teacher.user.refresh_from_db()

        assert teacher.is_active is False
        assert teacher.user.is_active is False