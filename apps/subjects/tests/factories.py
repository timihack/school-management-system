import factory
from factory.django import DjangoModelFactory

from apps.classes.models import ClassLevel
from apps.classes.tests.factories import ClassLevelFactory

from ..models import AssessmentComponent, GradeBand, GradingScale, SkillChecklistItem, Subject, Topic


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


class TopicFactory(DjangoModelFactory):
    """
    `term` is deliberately left unset (defaults to None) rather than
    wired to a SubFactory - Topic.term is nullable specifically for
    schools that don't want term-level granularity, and there's no
    confirmed apps.terms.tests.factories.TermFactory in evidence yet
    to safely wire up sight-unseen. Tests that need a real term should
    pass one explicitly: TopicFactory(term=SomeTermFactory()).

    `class_level` is independent of `subject` by default - NOT added
    to subject.class_levels. That's fine for model-level tests that
    create a Topic directly (the FK has no DB-level constraint tying
    it to the subject's class_levels; only TopicForm's queryset
    scoping enforces that, at the view layer). View-level tests going
    through TopicCreateView/TopicUpdateView must call
    subject.class_levels.add(class_level) first, or TopicForm's
    scoped dropdown will be empty and every POST will fail validation
    - this bit SubjectFactory's default (no class_levels) the first
    time through, so it's called out explicitly here.
    """

    class Meta:
        model = Topic

    subject = factory.SubFactory(SubjectFactory)
    class_level = factory.SubFactory(ClassLevelFactory)
    name = factory.Sequence(lambda n: f"Topic {n}")
    description = factory.Sequence(lambda n: f"Description {n}")
    order = 0