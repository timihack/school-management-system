from django.conf import settings
from django.db import models

from core.models import TimestampedModel


class Department(TimestampedModel):
    """
    Purely organizational - unlike every app so far (Students, Parents,
    Teachers, Staff), a Department has no linked User and no login. It's
    a grouping concept that Teacher and Staff profiles now reference,
    not a person. Reuses TimestampedModel (created_at/updated_at) from
    core/models.py - a small validation that abstraction is genuinely
    generic, not just useful for "employee" shaped things.

    No is_active field, deliberately: there's no login to disable and no
    historical person-record worth preserving via soft-delete the way
    Student/Parent/Teacher/Staff need. Deleting a Department is a real
    delete (see services.delete_department) - members get unassigned
    via SET_NULL, not cascade-deleted.
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    # FK to User (not Teacher or Staff specifically) because a
    # department head could be either - a plain User FK with a role
    # filter avoids needing a GenericForeignKey/ContentType setup for
    # what's really just "one of two possible profile types." The
    # limit_choices_to below is a SOFT constraint - it restricts what
    # Django's admin and ModelForm-generated querysets show, but doesn't
    # stop a direct ORM assignment. That's a deliberate proportionality
    # call: a bad head-of-department assignment is a low-stakes, easily
    # fixed data-quality issue, not an invariant worth a DB CHECK
    # constraint the way Guardianship's primary-contact rule was.
    head_of_department = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="departments_headed",
        limit_choices_to={"role__in": ["TEACHER", "STAFF"]},
        help_text="Must be an existing Teacher or Staff user.",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name