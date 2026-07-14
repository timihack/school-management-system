import datetime

import pytest

from apps.accounts.models import User
from apps.students.services import StudentCreateData, create_student, deactivate_student
from apps.students.tests.factories import StudentFactory


@pytest.mark.django_db
class TestCreateStudent:
    def test_creates_linked_user_and_student(self):
        data = StudentCreateData(
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
            admission_number="ADM00123",
            date_of_birth=datetime.date(2012, 5, 1),
            gender="FEMALE",
            admission_date=datetime.date.today(),
        )

        student, temporary_password = create_student(data)

        assert student.pk is not None
        assert student.user.role == User.Role.STUDENT
        assert student.user.email == "ada@example.com"
        assert student.user.check_password(temporary_password)

    def test_username_matches_admission_number(self):
        data = StudentCreateData(
            first_name="Grace",
            last_name="Hopper",
            email="grace@example.com",
            admission_number="ADM00456",
            date_of_birth=datetime.date(2011, 3, 15),
            gender="FEMALE",
            admission_date=datetime.date.today(),
        )

        student, _ = create_student(data)

        assert student.user.username == "ADM00456"


@pytest.mark.django_db
class TestDeactivateStudent:
    def test_deactivates_student_and_disables_login(self):
        student = StudentFactory()

        deactivate_student(student)
        student.refresh_from_db()
        student.user.refresh_from_db()

        assert student.is_active is False
        assert student.user.is_active is False