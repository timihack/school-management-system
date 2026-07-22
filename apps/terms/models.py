from django.core.validators import MinValueValidator
from django.db import models

from core.models import TimestampedModel


class AcademicSession(TimestampedModel):
    """
    A school year (e.g. "2024/2025"). Deliberately has NO is_current
    field of its own - see Term below for why. This is a pure
    organizational concept with no linked User, same category as
    Department (Phase 7) and ClassLevel (Phase 8).
    """

    name = models.CharField(max_length=20, unique=True, help_text="e.g. '2024/2025'.")
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ["-start_date"]

    def __str__(self) -> str:
        return self.name


class Term(TimestampedModel):
    """
    One term within an AcademicSession (First/Second/Third).

    is_current lives HERE, not on AcademicSession - having both would
    risk two independently-settable flags drifting out of sync (current
    session says one year, current term points at another). "Current
    session" is always DERIVED as current_term.academic_session (see
    selectors.get_current_session), never stored as a second flag.

    next_term_begins and total_school_days are both fields confirmed
    directly by a real report card (Elon College showed "Next Term
    begins: May 05, 2025" and an attendance figure "1 out of 120" -
    120 being the term's total school days) - not speculative additions.
    """

    class TermName(models.TextChoices):
        FIRST = "FIRST", "First Term"
        SECOND = "SECOND", "Second Term"
        THIRD = "THIRD", "Third Term"

    academic_session = models.ForeignKey(
        AcademicSession, on_delete=models.CASCADE, related_name="terms"
    )
    name = models.CharField(max_length=10, choices=TermName.choices)
    # Explicit integer for ordering/comparison (e.g. "is this the LAST
    # term of its session" - see selectors.is_last_term_of_session),
    # rather than relying on alphabetical sort of the TextChoices values
    # coincidentally matching chronological order.
    sequence = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    start_date = models.DateField()
    end_date = models.DateField()
    next_term_begins = models.DateField(null=True, blank=True)
    total_school_days = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1)]
    )
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ["academic_session__start_date", "sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["academic_session", "name"], name="unique_term_name_per_session"
            ),
            # Global singleton - there's only ever one "now" across the
            # whole school, not scoped per session. fields=["is_current"]
            # combined with condition=Q(is_current=True) is the standard
            # Django technique for a constraint with no natural scoping
            # field: among rows where is_current=True, the value of
            # is_current is trivially always True for all of them, so
            # uniqueness on that value means "at most one such row."
            models.UniqueConstraint(
                fields=["is_current"],
                condition=models.Q(is_current=True),
                name="unique_current_term",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_name_display()} - {self.academic_session.name}"