from django.db import transaction

from .models import AttendanceRecord
from .validators import validate_date_within_term


@transaction.atomic
def mark_attendance(
    *, class_level, class_arm=None, date, term, marked_by, attendance_data: dict
) -> list[AttendanceRecord]:
    """
    Bulk upsert: one AttendanceRecord per student in attendance_data
    (student_id -> status). class_arm is genuinely OPTIONAL - None for a
    class_level with has_arms=False, exactly mirroring how
    ClassEnrollment (Phase 8) represents "enrolled at a no-arm level."
    Nothing here treats a missing arm as a special/error case; it's
    just written through to the record as NULL.

    Idempotent by design - re-submitting the same class+date (e.g. a
    teacher correcting a mistake) updates the existing rows rather than
    creating duplicates or erroring on the
    unique_attendance_per_student_per_day constraint.

    validate_date_within_term runs BEFORE any writes, and the whole
    operation is wrapped in transaction.atomic - either every student's
    record for this date is written, or none are.
    """
    validate_date_within_term(date=date, term=term)

    records = []
    for student_id, status in attendance_data.items():
        record, _ = AttendanceRecord.objects.update_or_create(
            student_id=student_id,
            date=date,
            defaults={
                "class_level": class_level,
                "class_arm": class_arm,
                "term": term,
                "status": status,
                "marked_by": marked_by,
            },
        )
        records.append(record)

    return records