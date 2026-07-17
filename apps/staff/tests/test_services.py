import datetime

import pytest

from apps.accounts.models import User
from apps.staff.models import Staff
from apps.staff.services import StaffCreateData, create_staff, deactivate_staff
from apps.staff.tests.factories import StaffFactory


@pytest.mark.django_db
class TestCreateStaff:
    def test_creates_linked_user_and_staff(self):
        data = StaffCreateData(
            first_name="Grace",
            last_name="Hopper",
            email="grace.hopper@example.com",
            employee_id="STF00123",
            date_of_birth=datetime.date(1975, 12, 9),
            date_joined=datetime.date(2018, 4, 1),
            job_title="IT Support",
            employment_type=Staff.EmploymentType.FULL_TIME,
        )

        staff, temporary_password = create_staff(data)

        assert staff.pk is not None
        assert staff.user.role == User.Role.STAFF
        assert staff.user.check_password(temporary_password)
        assert staff.user.username == "STF00123"

    def test_defaults_to_full_time(self):
        data = StaffCreateData(
            first_name="Ada",
            last_name="Lovelace",
            email="ada.l@example.com",
            employee_id="STF00456",
            date_of_birth=datetime.date(1980, 1, 1),
            date_joined=datetime.date(2019, 1, 1),
        )

        staff, _ = create_staff(data)

        assert staff.employment_type == Staff.EmploymentType.FULL_TIME


@pytest.mark.django_db
class TestDeactivateStaff:
    def test_deactivates_staff_and_disables_login(self):
        staff = StaffFactory()

        deactivate_staff(staff)
        staff.refresh_from_db()
        staff.user.refresh_from_db()

        assert staff.is_active is False
        assert staff.user.is_active is False