import secrets
from dataclasses import dataclass
from datetime import date

from django.db import transaction

from apps.accounts.models import User
from apps.departments.models import Department

from .models import Staff


@dataclass
class StaffCreateData:
    first_name: str
    last_name: str
    email: str
    employee_id: str
    date_of_birth: date
    date_joined: date
    job_title: str = ""
    employment_type: str = Staff.EmploymentType.FULL_TIME
    phone_number: str = ""
    address: str = ""
    department: "Department | None" = None


def _generate_temporary_password() -> str:
    return secrets.token_urlsafe(10)


@transaction.atomic
def create_staff(data: StaffCreateData) -> tuple[Staff, str]:
    """Mirrors create_teacher()/create_student()/create_parent() - same reasoning throughout."""
    temporary_password = _generate_temporary_password()

    user = User.objects.create_user(
        username=data.employee_id,
        email=data.email,
        first_name=data.first_name,
        last_name=data.last_name,
        role=User.Role.STAFF,
        password=temporary_password,
    )

    staff = Staff.objects.create(
        user=user,
        employee_id=data.employee_id,
        job_title=data.job_title,
        employment_type=data.employment_type,
        date_of_birth=data.date_of_birth,
        date_joined=data.date_joined,
        phone_number=data.phone_number,
        address=data.address,
        department=data.department,
    )

    return staff, temporary_password


@transaction.atomic
def deactivate_staff(staff: Staff) -> Staff:
    staff.is_active = False
    staff.save(update_fields=["is_active", "updated_at"])

    staff.user.is_active = False
    staff.user.save(update_fields=["is_active"])

    return staff