import pytest

from apps.classes.models import ClassEnrollment, PromotionPolicy
from apps.classes.services import assign_student_to_class, ensure_promotion_policy_exists
from apps.classes.tests.factories import ClassArmFactory, ClassLevelFactory
from apps.students.tests.factories import StudentFactory


@pytest.mark.django_db
class TestEnsurePromotionPolicyExists:
    def test_creates_policy_with_defaults(self):
        level = ClassLevelFactory()

        policy = ensure_promotion_policy_exists(level)

        assert policy.pk is not None
        assert policy.class_level == level

    def test_is_idempotent(self):
        level = ClassLevelFactory()

        first = ensure_promotion_policy_exists(level)
        second = ensure_promotion_policy_exists(level)

        assert first.pk == second.pk
        assert PromotionPolicy.objects.filter(class_level=level).count() == 1


@pytest.mark.django_db
class TestAssignStudentToClass:
    def test_creates_current_enrollment(self):
        student = StudentFactory()
        arm = ClassArmFactory()

        enrollment = assign_student_to_class(
            student=student, class_level=arm.class_level, class_arm=arm
        )

        assert enrollment.is_current is True
        assert enrollment.class_arm == arm

    def test_reassignment_retires_the_previous_current_enrollment(self):
        """
        The core guarantee this phase depends on: the conditional
        UniqueConstraint on ClassEnrollment would reject a second
        is_current=True row outright if the service didn't clear the
        first one before inserting - same mechanism as
        link_guardianship()'s primary-contact handling in Phase 4.
        """
        student = StudentFactory()
        arm_a = ClassArmFactory()
        arm_b = ClassArmFactory(class_level=arm_a.class_level)

        first = assign_student_to_class(
            student=student, class_level=arm_a.class_level, class_arm=arm_a
        )
        second = assign_student_to_class(
            student=student, class_level=arm_a.class_level, class_arm=arm_b
        )

        first.refresh_from_db()
        assert first.is_current is False
        assert second.is_current is True
        assert ClassEnrollment.objects.filter(student=student, is_current=True).count() == 1

    def test_is_repeat_flag_is_stored(self):
        student = StudentFactory()
        arm = ClassArmFactory()

        enrollment = assign_student_to_class(
            student=student, class_level=arm.class_level, class_arm=arm, is_repeat=True
        )

        assert enrollment.is_repeat is True