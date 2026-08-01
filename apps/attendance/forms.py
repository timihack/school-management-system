from apps.attendance.models import AttendanceRecord


def parse_attendance_submission(post_data, student_ids: list[int]) -> dict[int, str]:
    """
    Parses a bulk attendance register submission into {student_id: status}.

    Deliberately a plain function, not a Django Form subclass: a
    register has one status field PER STUDENT IN THE ROSTER, and the
    roster's size varies by arm (10 students today, 40 tomorrow) - a
    Form's field set is fixed at class-definition time and doesn't fit a
    genuinely variable field count. Each status input is named
    "status_<student_id>" in the template; this function reads those
    back out and validates each value against AttendanceRecord.Status,
    defaulting anything missing or invalid to PRESENT (the same
    "assume present unless marked otherwise" default most physical
    paper registers use).
    """
    valid_statuses = {choice for choice, _ in AttendanceRecord.Status.choices}
    result = {}

    for student_id in student_ids:
        raw_value = post_data.get(f"status_{student_id}", AttendanceRecord.Status.PRESENT)
        result[student_id] = raw_value if raw_value in valid_statuses else AttendanceRecord.Status.PRESENT

    return result