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


@pytest.mark.django_db
class TestAssignStudentToClassSessionAutoPopulation:
    """
    Covers the Phase 10 retrofit: academic_session defaults to whatever
    apps.terms.selectors.get_current_session() returns, unless an
    explicit one is passed. This is the actual proof that the deferred
    FK added in Phase 10 does something, not just that the column
    exists.
    """

    def test_defaults_to_the_current_session_when_one_is_active(self):
        from apps.terms.services import activate_term
        from apps.terms.tests.factories import TermFactory

        term = TermFactory()
        activate_term(term)
        student = StudentFactory()
        arm = ClassArmFactory()

        enrollment = assign_student_to_class(
            student=student, class_level=arm.class_level, class_arm=arm
        )

        assert enrollment.academic_session == term.academic_session

    def test_is_none_when_no_session_is_current(self):
        student = StudentFactory()
        arm = ClassArmFactory()

        enrollment = assign_student_to_class(
            student=student, class_level=arm.class_level, class_arm=arm
        )

        assert enrollment.academic_session is None

    def test_explicit_academic_session_overrides_the_current_one(self):
        from apps.terms.services import activate_term
        from apps.terms.tests.factories import AcademicSessionFactory, TermFactory

        current_term = TermFactory()
        activate_term(current_term)
        other_session = AcademicSessionFactory(name="1999/2000")
        student = StudentFactory()
        arm = ClassArmFactory()

        enrollment = assign_student_to_class(
            student=student,
            class_level=arm.class_level,
            class_arm=arm,
            academic_session=other_session,
        )

        assert enrollment.academic_session == other_session