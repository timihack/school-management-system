from django.conf import settings
from django.db import models

from core.models import EmploymentProfileBase


class Staff(EmploymentProfileBase):
    """
    Non-teaching school employees (admin, library, IT, maintenance,
    security, etc.). Shares its entire employment "shape" with Teacher
    via EmploymentProfileBase - what's genuinely different is captured
    below:

    - job_title: a free-text role name. Teacher has no equivalent -
      "Teacher" IS the role; what varies is qualification/specialty.
      For Staff, the role itself varies (Librarian, Accountant, IT
      Support, Security Guard, ...), so it needs its own field.
    - employment_type: full-time/part-time/contract. Teacher doesn't
      model this distinction at all in this system - teaching staff are
      treated as uniformly full-time for now. Staff realistically
      includes part-time and contract roles (cleaning, security) far
      more often, so this earns its own field here.

    No Department FK yet, for the same reason Teacher has no
    Department/Subject/Class FK: the Departments module doesn't exist
    yet in this project's build order.
    """

    class EmploymentType(models.TextChoices):
        FULL_TIME = "FULL_TIME", "Full-time"
        PART_TIME = "PART_TIME", "Part-time"
        CONTRACT = "CONTRACT", "Contract"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="staff_profile",
    )
    job_title = models.CharField(max_length=100, blank=True)
    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME,
    )

    class Meta:
        ordering = ["employee_id"]

    def __str__(self) -> str:
        return f"{self.user.get_full_name() or self.user.username} ({self.employee_id})"