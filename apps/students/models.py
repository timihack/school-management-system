from django.conf import settings
from django.db import models


class Student(models.Model):
  """
  Extends the custom User (role=STUDENT) with student-specific domain
  data. Identity fields (name, email, login credentials) stay on User -
  this model never duplicates them, only adds what a User alone
  doesn't capture.

  NOTE: no FK to a "class"/"grade" yet - the Classes app doesn't exist
  yet (it comes later in the module order). Adding that FK now would
  mean guessing at a schema we haven't designed. It gets added via a
  migration on THIS model once the Classes app exists, which is the
  normal, expected way schemas evolve - not a shortcut being taken now.
  """

  class Gender(models.TextChoices):
    MALE = "MALE", "Male"
    FEMALE = "FEMALE", "Female"
    # OTHER = "OTHER", "Other"

  user = models.OneToOneField(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name="student_profile",
  )
  admission_number = models.CharField(max_length=20, unique=True, db_index=True)
  date_of_birth = models.DateField()
  gender = models.CharField(max_length=10, choices=Gender.choices)
  admission_date = models.DateField()
  address = models.TextField(blank=True)
  phone_number = models.CharField(max_length=20, blank=True)
  is_active = models.BooleanField(default=True)

  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    ordering  = ["admission_number"]

  def __str__(self) -> str:
    return f"{self.user.get_full_name() or self.user.username} ({self.admission_number})"