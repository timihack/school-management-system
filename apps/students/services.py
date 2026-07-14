import secrets
from dataclasses import dataclass
from datetime import date

from django.db import transaction

from apps.accounts.models import User
from .models import Student


@dataclass
class StudentCreateData:
  first_name: str
  last_name: str
  email: str
  admission_number: str
  date_of_birth: date
  gender: str
  admission_date: date
  address: str = ""
  phone_number: str = ""


def _generate_temporary_password() -> str:
  return secrets.token_urlsafe(10)


@transaction.atomic
def create_student(data: StudentCreateData) -> tuple[Student, str]:
  """
  Creates BOTH the login-capable User (role=STUDENT) and the Student
  profile atomically. A Student without a way to log in, or a User
  with role=STUDENT but no Student profile, would be an invalid
  half-created state - transaction.atomic guarantees we never end up
  with one but not the other, even if something fails partway through.

  Returns the temporary password so the caller (the view) can display
  it ONCE to the admin creating the account. It is never stored in
  plaintext or logged anywhere - only the hashed version lives on User.
  """
  temporary_password = _generate_temporary_password()

  user = User.objects.create_user(
    username=data.admission_number,
    email=data.email,
    first_name=data.first_name,
    last_name=data.last_name,
    role=User.Role.STUDENT,
    password=temporary_password,
  )

  student = Student.objects.create(
    user=user,
    admission_number=data.admission_number,
    date_of_birth=data.date_of_birth,
    gender=data.gender,
    admission_date=data.admission_date,
    address=data.address,
    phone_number=data.phone_number,
  )

  return student, temporary_password


@transaction.atomic
def deactivate_student(student: Student) -> Student:
  """
  Soft-disable rather than delete: preserves attendance/exam/fee
  history that later modules will attach to this student. Also
  disables login via the linked User, since a withdrawn/graduated
  student shouldn't be able to sign in even though their record stays.
  """
  student.is_active = False
  student.save(update_fields=["is_active", "updated_at"])

  student.user.is_active = False
  student.user.save(update_fields=["is_active"])

  return student