import secrets
from dataclasses import dataclass

from django.db import transaction

from apps.accounts.models import User
from apps.students.models import Student

from .models import Guardianship, Parent


@dataclass
class ParentCreateData:
    first_name: str
    last_name: str
    email: str
    occupation: str = ""
    address: str = ""
    phone_number: str = ""


def _generate_temporary_password() -> str:
    return secrets.token_urlsafe(10)


@transaction.atomic
def create_parent(data: ParentCreateData) -> tuple[Parent, str]:
  """
  Mirrors create_student(): creates BOTH the login-capable User
  (role=PARENT) and the Parent profile atomically. Unlike a student,
  a parent has no natural "admission number" to use as a username, so
  one is derived from the email's local part plus a short random
  suffix - unique, and still recognisable to whoever's reading a user
  list later (unlike a bare random token).
  """
  temporary_password = _generate_temporary_password()
  username = f"{data.email.split('@')[0]}.{secrets.token_hex(3)}"

  user = User.objects.create_user(
    username=username,
    email=data.email,
    first_name=data.first_name,
    last_name=data.last_name,
    role=User.Role.PARENT,
    password=temporary_password,
  )

  parent = Parent.objects.create(
    user=user,
    occupation=data.occupation,
    address=data.address,
    phone_number=data.phone_number,
  )

  return parent, temporary_password


@transaction.atomic
def deactivate_parent(parent: Parent) -> Parent:
    parent.is_active = False
    parent.save(update_fields=["is_active", "updated_at"])

    parent.user.is_active = False
    parent.user.save(update_fields=["is_active"])

    return parent


@transaction.atomic
def link_guardianship(
  *,
  parent: Parent,
  student: Student,
  relationship: str,
  is_primary_contact: bool = False,
  can_pickup: bool = True,
) -> Guardianship:
  """
  Links an EXISTING parent to an EXISTING student - this never creates
  either side, only the relationship between them.

  If marked as primary contact, clears any OTHER primary-contact flag
  for this student first. The database's conditional UniqueConstraint
  (see models.py) would otherwise reject the insert outright - this
  isn't a nicety, it's what makes the create actually succeed.
  """
  if is_primary_contact:
      Guardianship.objects.filter(student=student, is_primary_contact=True).update(
          is_primary_contact=False
      )

  return Guardianship.objects.create(
    parent=parent,
    student=student,
    relationship=relationship,
    is_primary_contact=is_primary_contact,
    can_pickup=can_pickup,
  )


def unlink_guardianship(guardianship: Guardianship) -> None:
    guardianship.delete()