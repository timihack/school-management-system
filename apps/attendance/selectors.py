from django.db.models import QuerySet

from apps.classes.selectors import get_current_students_in_arm, get_current_students_in_level

from .models import AttendanceRecord


def get_roster(*, class_level, class_arm=None):
    """
    THE single roster-resolution function for taking attendance -
    deliberately branches on whether class_arm is provided, mirroring
    exactly how ClassEnrollment (Phase 8) already treats "class_arm is
    None" as the normal, valid representation of a no-arm level, not an
    error case needing special handling everywhere it's touched.
    """
    if class_arm is not None:
        return get_current_students_in_arm(class_arm)
    return get_current_students_in_level(class_level)


def get_attendance_for_date(*, class_level, class_arm=None, date) -> QuerySet[AttendanceRecord]:
    """
    Existing records for a given date - used to pre-fill the register
    form when correcting a day that's already been marked. Filters by
    class_level always; class_arm is an ADDITIONAL filter only applied
    when provided, since a no-arm level's records have class_arm=NULL.
    """
    qs = AttendanceRecord.objects.filter(class_level=class_level, date=date)
    if class_arm is not None:
        qs = qs.filter(class_arm=class_arm)
    return qs.select_related("student__user")


def get_attendance_summary_for_student(student, term) -> dict:
    """
    Powers the "X out of Y school days" figure confirmed by a real
    report card (Elon College: "1 out of 120") - X here is
    days_absent, matched against term.total_school_days as the
    denominator. Unaffected by whether the student's class has arms -
    this queries by student and term, not by class_arm at all.
    """
    records = AttendanceRecord.objects.filter(student=student, term=term)

    return {
        "days_present": records.filter(status=AttendanceRecord.Status.PRESENT).count(),
        "days_absent": records.filter(status=AttendanceRecord.Status.ABSENT).count(),
        "days_late": records.filter(status=AttendanceRecord.Status.LATE).count(),
        "days_excused": records.filter(status=AttendanceRecord.Status.EXCUSED).count(),
        "total_school_days": term.total_school_days,
    }