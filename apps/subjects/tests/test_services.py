import pytest

from apps.classes.tests.factories import ClassLevelFactory
from apps.subjects.models import AssessmentComponent, GradingScale
from apps.subjects.services import ensure_grading_scale_exists
from apps.subjects.tests.factories import AssessmentComponentFactory, SubjectFactory


@pytest.mark.django_db
class TestSubjectMaxScoreProperties:
    def test_ca_and_exam_totals_and_overall(self):
        subject = SubjectFactory()
        AssessmentComponentFactory(
            subject=subject, name="CA1", component_type=AssessmentComponent.ComponentType.CA, max_score=10
        )
        AssessmentComponentFactory(
            subject=subject, name="CA2", component_type=AssessmentComponent.ComponentType.CA, max_score=10
        )
        AssessmentComponentFactory(
            subject=subject,
            name="CA3",
            component_type=AssessmentComponent.ComponentType.CA,
            max_score=20,
        )
        AssessmentComponentFactory(
            subject=subject,
            name="Exam",
            component_type=AssessmentComponent.ComponentType.EXAM,
            max_score=60,
        )

        assert subject.ca_max_total == 40
        assert subject.exam_max_total == 60
        assert subject.overall_max_score == 100

    def test_different_subjects_can_have_different_totals(self):
        """
        Directly validates the assumption behind the overall promotion
        percentage formula in docs/ACADEMIC_STRUCTURE_REQUIREMENTS.md
        Section 3 - subjects are allowed to have different max totals,
        which is exactly why that formula sums MAX across subjects
        rather than assuming a flat 100 each.
        """
        subject_a = SubjectFactory()
        AssessmentComponentFactory(subject=subject_a, max_score=100, component_type=AssessmentComponent.ComponentType.EXAM)

        subject_b = SubjectFactory()
        AssessmentComponentFactory(subject=subject_b, max_score=50, component_type=AssessmentComponent.ComponentType.EXAM)

        assert subject_a.overall_max_score == 100
        assert subject_b.overall_max_score == 50

    def test_totals_are_zero_when_no_components_defined(self):
        subject = SubjectFactory()

        assert subject.ca_max_total == 0
        assert subject.exam_max_total == 0
        assert subject.overall_max_score == 0


@pytest.mark.django_db
class TestEnsureGradingScaleExists:
    def test_creates_scale(self):
        level = ClassLevelFactory()

        scale = ensure_grading_scale_exists(level)

        assert scale.pk is not None
        assert scale.class_level == level

    def test_is_idempotent(self):
        level = ClassLevelFactory()

        first = ensure_grading_scale_exists(level)
        second = ensure_grading_scale_exists(level)

        assert first.pk == second.pk
        assert GradingScale.objects.filter(class_level=level).count() == 1