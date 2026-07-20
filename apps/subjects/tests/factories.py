import factory
from factory.django import DjangoModelFactory

from apps.classes.models import ClassLevel
from apps.classes.tests.factories import ClassLevelFactory

from ..models import AssessmentComponent, GradeBand, GradingScale, SkillChecklistItem, Subject


class SubjectFactory(DjangoModelFactory):
    class Meta:
        model = Subject
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Subject {n}")
    code = factory.Sequence(lambda n: f"SUB{n}")
    assessment_type = ClassLevel.AssessmentType.SCORE_BASED


class AssessmentComponentFactory(DjangoModelFactory):
    class Meta:
        model = AssessmentComponent

    subject = factory.SubFactory(SubjectFactory)
    name = factory.Sequence(lambda n: f"CA{n}")
    component_type = AssessmentComponent.ComponentType.CA
    max_score = 10
    order = 0


class SkillChecklistItemFactory(DjangoModelFactory):
    class Meta:
        model = SkillChecklistItem

    subject = factory.SubFactory(SubjectFactory, assessment_type=ClassLevel.AssessmentType.SKILL_BASED)
    description = factory.Sequence(lambda n: f"Skill {n}")


class GradingScaleFactory(DjangoModelFactory):
    class Meta:
        model = GradingScale

    class_level = factory.SubFactory(ClassLevelFactory)


class GradeBandFactory(DjangoModelFactory):
    class Meta:
        model = GradeBand

    grading_scale = factory.SubFactory(GradingScaleFactory)
    label = "A"
    min_percentage = 75
    max_percentage = 100