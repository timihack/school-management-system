from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
  """
  Custom user model — the single identity record for every human in the
  system (admin, teacher, student, parent, staff). Role-specific profile
  data (e.g. StudentProfile, TeacherProfile) will live in their own apps
  later and link back here via OneToOneField. This model itself only
  holds identity + RBAC role, nothing domain-specific.
  """
  
  class Role(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    TEACHER = "TEACHER", "Teacher"
    STUDENT = "STUDENT", "Student"
    PARENT = "PARENT", "Parent"
    STAFF = "STAFF", "Staff"

  role = models.CharField(
    max_length=20,
    choices=Role.choices,
    default=Role.STUDENT,
  )

  # Makes `createsuperuser` prompt for role explicitly, instead of every
  # superuser silently defaulting to role=STUDENT while is_staff=True -
  # a mismatch that would pass Django admin's own checks but fail our
  # RoleRequiredMixin/role_required checks confusingly.
  REQUIRED_FIELDS = ["email", "role"]

  def __str__(self):
    return f"{self.get_full_name() or self.username} ({self.role})"