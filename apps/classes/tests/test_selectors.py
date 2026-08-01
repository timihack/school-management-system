import pytest

from apps.classes.selectors import get_current_students_in_arm, get_current_students_in_level
from apps.classes.services import assign_student_to_class
from apps.classes.tests.factories import ClassArmFactory, ClassLevelFactory
from apps.students.models import Student
from apps.students.tests.factories import StudentFactory


@pytest.mark.django_db
class TestGetCurrentStudentsInArm:
    def test_returns_actual_student_instances_not_enrollment_rows(self):
        """
        Regression test for a real bug: this previously returned
        QuerySet[ClassEnrollment] despite its name promising Students -
        apps.attendance's code treated each row's .pk as a STUDENT pk,
        when it was actually the enrollment row's own pk. Asserting the
        instance TYPE here, not just that "something" comes back, is
        what actually catches a regression back to that bug.
        """
        arm = ClassArmFactory()
        student = StudentFactory()
        assign_student_to_class(student=student, class_level=arm.class_level, class_arm=arm)

        result = list(get_current_students_in_arm(arm))

        assert len(result) == 1
        assert isinstance(result[0], Student)
        assert result[0].pk == student.pk


@pytest.mark.django_db
class TestGetCurrentStudentsInLevel:
    def test_returns_students_enrolled_directly_at_a_no_arm_level(self):
        level = ClassLevelFactory(has_arms=False)
        student = StudentFactory()
        assign_student_to_class(student=student, class_level=level, class_arm=None)

        result = list(get_current_students_in_level(level))

        assert len(result) == 1
        assert isinstance(result[0], Student)
        assert result[0].pk == student.pk

    def test_does_not_include_students_enrolled_in_an_arm_of_the_same_level(self):
        """
        A level can have SOME students with no arm and, in principle,
        arms too - this confirms get_current_students_in_level only
        returns the arm-less ones, not everyone at the level regardless
        of arm.
        """
        level = ClassLevelFactory(has_arms=True)
        arm = ClassArmFactory(class_level=level)
        student_with_arm = StudentFactory()
        student_without_arm = StudentFactory()
        assign_student_to_class(student=student_with_arm, class_level=level, class_arm=arm)
        assign_student_to_class(student=student_without_arm, class_level=level, class_arm=None)

        result = list(get_current_students_in_level(level))

        assert len(result) == 1
        assert result[0].pk == student_without_arm.pk