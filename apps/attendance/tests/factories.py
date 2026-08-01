import datetime

import factory
from factory.django import DjangoModelFactory

from apps.classes.tests.factories import ClassArmFactory
from apps.students.tests.factories import StudentFactory
from apps.terms.tests.factories import TermFactory

from ..models import AttendanceRecord


class AttendanceRecordFactory(DjangoModelFactory):
    """
    Defaults to an ARM-based record (class_level derived from the arm's
    own level) since that's the more common case to exercise casually -
    tests specifically covering the no-arm path pass class_arm=None and
    an explicit class_level instead.
    """

    class Meta:
        model = AttendanceRecord

    student = factory.SubFactory(StudentFactory)
    class_arm = factory.SubFactory(ClassArmFactory)
    class_level = factory.LazyAttribute(lambda record: record.class_arm.class_level)
    term = factory.SubFactory(TermFactory)
    date = datetime.date(2024, 9, 10)
    status = AttendanceRecord.Status.PRESENT