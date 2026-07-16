from django.conf import settings
from django.db import models


class Teacher(models.Model):
    """
    Extends the custom User (role=TEACHER) with teacher-specific domain
    data - same "profile" pattern as Student and Parent.

    Deliberately scoped to identity + employment fields ONLY. No FK to
    a Department, Subject, or Class exists here, because none of those
    apps exist yet (they come later in the module order). Adding those
    relationships now would mean guessing at schemas that haven't been
    designed - exactly the reasoning that kept Student's Class FK out of
    Phase 3. They'll be added via a migration on THIS model once each
    target app exists.

    Also deliberately NOT sharing a base class with the future Staff
    model, even though the two will likely have near-identical fields -
    see this phase's write-up for why guessing that abstraction now
    would be premature.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_profile",
    )
    employee_id = models.CharField(max_length=20, unique=True, db_index=True)
    qualification = models.CharField(
        max_length=200,
        blank=True,
        help_text="Free text for now, e.g. 'B.Ed, M.Sc Mathematics'.",
    )
    date_of_birth = models.DateField()
    date_joined = models.DateField()
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["employee_id"]

    def __str__(self) -> str:
        return f"{self.user.get_full_name() or self.user.username} ({self.employee_id})"