import secrets
from dataclasses import dataclass
from datetime import date

from django.db import transaction

from apps.accounts.models import User

from .models import Teacher


@dataclass
class TeacherCreateData:
    first_name: str
    last_name: str
    email: str
    employee_id: str
    date_of_birth: date
    date_joined: date
    qualification: str = ""
    phone_number: str = ""
    address: str = ""


def _generate_temporary_password() -> str:
    return secrets.token_urlsafe(10)


@transaction.atomic
def create_teacher(data: TeacherCreateData) -> tuple[Teacher, str]:
    """Mirrors create_student()/create_parent() - same reasoning throughout."""
    temporary_password = _generate_temporary_password()

    user = User.objects.create_user(
        username=data.employee_id,
        email=data.email,
        first_name=data.first_name,
        last_name=data.last_name,
        role=User.Role.TEACHER,
        password=temporary_password,
    )

    teacher = Teacher.objects.create(
        user=user,
        employee_id=data.employee_id,
        qualification=data.qualification,
        date_of_birth=data.date_of_birth,
        date_joined=data.date_joined,
        phone_number=data.phone_number,
        address=data.address,
    )

    return teacher, temporary_password


@transaction.atomic
def deactivate_teacher(teacher: Teacher) -> Teacher:
    teacher.is_active = False
    teacher.save(update_fields=["is_active", "updated_at"])

    teacher.user.is_active = False
    teacher.user.save(update_fields=["is_active"])

    return teacher