import datetime

import pytest
from django.core.exceptions import ValidationError

from apps.attendance.models import AttendanceRecord
from apps.attendance.services import mark_attendance
from apps.classes.services import assign_student_to_class
from apps.classes.tests.factories import ClassArmFactory, ClassLevelFactory
from apps.students.tests.factories import StudentFactory
from apps.terms.tests.factories import TermFactory


@pytest.mark.django_db
class TestMarkAttendanceArmBased:
    def test_creates_one_record_per_student(self):
        arm = ClassArmFactory()
        term = TermFactory(start_date=datetime.date(2024, 9, 1), end_date=datetime.date(2024, 12, 15))
        student_a = StudentFactory()
        student_b = StudentFactory()
        assign_student_to_class(student=student_a, class_level=arm.class_level, class_arm=arm)
        assign_student_to_class(student=student_b, class_level=arm.class_level, class_arm=arm)

        records = mark_attendance(
            class_level=arm.class_level,
            class_arm=arm,
            date=datetime.date(2024, 9, 10),
            term=term,
            marked_by=None,
            attendance_data={
                student_a.pk: AttendanceRecord.Status.PRESENT,
                student_b.pk: AttendanceRecord.Status.ABSENT,
            },
        )

        assert len(records) == 2
        assert AttendanceRecord.objects.filter(student=student_a, status="PRESENT").exists()
        assert AttendanceRecord.objects.filter(student=student_b, status="ABSENT").exists()
        # Every record correctly stores BOTH the level and the arm.
        assert records[0].class_level == arm.class_level
        assert records[0].class_arm == arm

    def test_resubmitting_the_same_day_updates_rather_than_duplicates(self):
        arm = ClassArmFactory()
        term = TermFactory(start_date=datetime.date(2024, 9, 1), end_date=datetime.date(2024, 12, 15))
        student = StudentFactory()
        assign_student_to_class(student=student, class_level=arm.class_level, class_arm=arm)
        the_date = datetime.date(2024, 9, 10)

        mark_attendance(
            class_level=arm.class_level, class_arm=arm, date=the_date, term=term, marked_by=None,
            attendance_data={student.pk: AttendanceRecord.Status.ABSENT},
        )
        mark_attendance(
            class_level=arm.class_level, class_arm=arm, date=the_date, term=term, marked_by=None,
            attendance_data={student.pk: AttendanceRecord.Status.PRESENT},
        )

        assert AttendanceRecord.objects.filter(student=student, date=the_date).count() == 1
        assert AttendanceRecord.objects.get(student=student, date=the_date).status == "PRESENT"

    def test_date_outside_term_is_rejected(self):
        arm = ClassArmFactory()
        term = TermFactory(start_date=datetime.date(2024, 9, 1), end_date=datetime.date(2024, 12, 15))
        student = StudentFactory()

        with pytest.raises(ValidationError):
            mark_attendance(
                class_level=arm.class_level,
                class_arm=arm,
                date=datetime.date(2025, 1, 5),  # after term.end_date
                term=term,
                marked_by=None,
                attendance_data={student.pk: AttendanceRecord.Status.PRESENT},
            )


@pytest.mark.django_db
class TestMarkAttendanceNoArmLevel:
    """
    Covers the corrected behavior: a ClassLevel with has_arms=False has
    NO ClassArm at all - attendance must still work for it, with
    class_arm simply stored as NULL, exactly mirroring how
    ClassEnrollment already represents this.
    """

    def test_records_are_created_with_a_null_class_arm(self):
        level = ClassLevelFactory(has_arms=False)
        term = TermFactory(start_date=datetime.date(2024, 9, 1), end_date=datetime.date(2024, 12, 15))
        student = StudentFactory()
        assign_student_to_class(student=student, class_level=level, class_arm=None)

        records = mark_attendance(
            class_level=level,
            class_arm=None,
            date=datetime.date(2024, 9, 10),
            term=term,
            marked_by=None,
            attendance_data={student.pk: AttendanceRecord.Status.PRESENT},
        )

        assert len(records) == 1
        assert records[0].class_level == level
        assert records[0].class_arm is None

    def test_summary_works_identically_regardless_of_arms(self):
        from apps.attendance.selectors import get_attendance_summary_for_student

        level = ClassLevelFactory(has_arms=False)
        term = TermFactory(start_date=datetime.date(2024, 9, 1), end_date=datetime.date(2024, 12, 15))
        student = StudentFactory()
        assign_student_to_class(student=student, class_level=level, class_arm=None)

        mark_attendance(
            class_level=level, class_arm=None, date=datetime.date(2024, 9, 10), term=term,
            marked_by=None, attendance_data={student.pk: AttendanceRecord.Status.ABSENT},
        )

        summary = get_attendance_summary_for_student(student, term)

        assert summary["days_absent"] == 1