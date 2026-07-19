import factory
from factory.django import DjangoModelFactory

from ..models import ClassArm, ClassLevel


class ClassLevelFactory(DjangoModelFactory):
    class Meta:
        model = ClassLevel
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Level {n}")
    category = ClassLevel.Category.JUNIOR_SECONDARY
    order = factory.Sequence(lambda n: n + 1)
    has_arms = True
    assessment_type = ClassLevel.AssessmentType.SCORE_BASED


class ClassArmFactory(DjangoModelFactory):
    class Meta:
        model = ClassArm

    class_level = factory.SubFactory(ClassLevelFactory)
    name = factory.Sequence(lambda n: f"Arm{n}")