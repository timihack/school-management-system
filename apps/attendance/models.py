from django.conf import settings
from django.db import models

from core.models import TimestampedModel


class AttendanceRecord(TimestampedModel):
    """
    One row per student per calendar day. class_level and class_arm are
    stored DIRECTLY on the record - not derived from the student's
    CURRENT enrollment - for the same historical-accuracy reason
    ClassEnrollment itself exists as a standalone history-preserving
    model (Phase 8): if a student later changes arms, their past
    attendance must still show which class they were actually in AT THE
    TIME, not wherever they are now.

    class_level is REQUIRED; class_arm is OPTIONAL - this mirrors
    ClassEnrollment's exact shape (Phase 8) for the exact same reason:
    docs/ACADEMIC_STRUCTURE_REQUIREMENTS.md Section 1 confirms arms are
    optional per level, and a level with has_arms=False has no ClassArm
    at all to attach a record to. CORRECTED from this app's original
    design, which made class_arm required - silently assuming every
    class has arms, which isn't true and isn't meant to be.

    PROTECT on class_level, class_arm, and term for the same reason
    ClassEnrollment.class_level is PROTECT (Phase 8) - losing which
    class/term a historical attendance record belonged to is a real data
    loss, not a cosmetic inconvenience, so deleting a ClassLevel,
    ClassArm, or Term that has any attendance history is blocked
    outright.
    """

    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"
        LATE = "LATE", "Late"
        EXCUSED = "EXCUSED", "Excused"

    student = models.ForeignKey(
        "students.Student", on_delete=models.CASCADE, related_name="attendance_records"
    )
    class_level = models.ForeignKey(
        "classes.ClassLevel", on_delete=models.PROTECT, related_name="attendance_records"
    )
    class_arm = models.ForeignKey(
        "classes.ClassArm",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="attendance_records",
        help_text="Null when class_level.has_arms is False.",
    )
    term = models.ForeignKey(
        "terms.Term", on_delete=models.PROTECT, related_name="attendance_records"
    )
    date = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PRESENT)
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_marked",
    )
    remarks = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "date"], name="unique_attendance_per_student_per_day"
            )
        ]

    def __str__(self) -> str:
        return f"{self.student} - {self.date} - {self.get_status_display()}"