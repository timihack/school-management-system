import pytest

from apps.classes.models import ClassLevel, PromotionPolicy
from apps.classes.services import ensure_promotion_policy_exists
from apps.classes.tests.factories import ClassLevelFactory
from apps.subjects.models import AssessmentComponent, Subject
from apps.subjects.tests.factories import (
    AssessmentComponentFactory,
    SkillChecklistItemFactory,
    SubjectFactory,
)


@pytest.mark.django_db
class TestComputationMethodConfiguration:
    def test_default_is_sum_components(self):
        subject = SubjectFactory()

        assert subject.computation_method == Subject.ComputationMethod.SUM_COMPONENTS

    def test_average_method_can_be_set(self):
        subject = SubjectFactory(computation_method=Subject.ComputationMethod.AVERAGE_CA_AND_EXAM)

        assert subject.computation_method == Subject.ComputationMethod.AVERAGE_CA_AND_EXAM


@pytest.mark.django_db
class TestSubjectCanHaveBothComponentsAndSkillItems:
    """
    Confirms the decoupling decision made after reviewing real report
    cards (AOS Montessori showed domains with BOTH a numeric CA/Exam/
    Total row AND a skill checklist underneath). The database never
    actually enforced exclusivity - this test makes that guarantee
    explicit and permanent, not just an accident of omission.
    """

    def test_a_single_subject_can_have_both(self):
        subject = SubjectFactory()
        AssessmentComponentFactory(subject=subject, name="CA", max_score=40)
        SkillChecklistItemFactory(subject=subject, description="Can identify 1-10")

        assert subject.assessment_components.count() == 1
        assert subject.skill_items.count() == 1


@pytest.mark.django_db
class TestCumulativeMethodConfiguration:
    def test_default_is_simple_average(self):
        level = ClassLevelFactory()

        policy = ensure_promotion_policy_exists(level)

        assert policy.cumulative_method == PromotionPolicy.CumulativeMethod.SIMPLE_AVERAGE

    def test_recursive_brought_forward_can_be_set(self):
        level = ClassLevelFactory()
        policy = ensure_promotion_policy_exists(level)

        policy.cumulative_method = PromotionPolicy.CumulativeMethod.RECURSIVE_BROUGHT_FORWARD
        policy.save()
        policy.refresh_from_db()

        assert policy.cumulative_method == PromotionPolicy.CumulativeMethod.RECURSIVE_BROUGHT_FORWARD