from django.conf import settings
from django.db import models

from core.models import EmploymentProfileBase


class Teacher(EmploymentProfileBase):
    """
    Refactored in Phase 6: employee_id, date_of_birth, date_joined,
    phone_number, address, is_active, created_at, updated_at now come
    from EmploymentProfileBase instead of being declared here directly.
    See core/models.py for why this extraction is justified now, and
    wasn't when this model was first written in Phase 5.

    qualification stays here, not in the shared base - it's specific to
    what a TEACHER needs, with no Staff equivalent (Staff has
    job_title + employment_type instead, which have no Teacher
    equivalent either).
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_profile",
    )
    qualification = models.CharField(
        max_length=200,
        blank=True,
        help_text="Free text for now, e.g. 'B.Ed, M.Sc Mathematics'.",
    )

    class Meta:
        ordering = ["employee_id"]

    def __str__(self) -> str:
        return f"{self.user.get_full_name() or self.user.username} ({self.employee_id})"