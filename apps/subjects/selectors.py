from django.db.models import Q, QuerySet

from .models import GradeBand, GradingScale, Subject, Topic


def get_subject_list(*, search: str = "", is_active: bool | None = None) -> QuerySet[Subject]:
    qs = Subject.objects.all()

    if is_active is not None:
        qs = qs.filter(is_active=is_active)

    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search))

    return qs


def get_components_for_subject(subject: Subject):
    return subject.assessment_components.all()


def get_skill_items_for_subject(subject: Subject):
    return subject.skill_items.all()


def get_grade_for_percentage(class_level, percentage: float) -> GradeBand | None:
    """
    Looks up which grade band a percentage falls into for a given class
    level's grading scale. Returns None if the level has no grading
    scale configured yet, or if the percentage falls in an unconfigured
    gap between bands (overlap is prevented by
    validators.validate_grade_band_does_not_overlap, but gaps are NOT
    currently prevented - a deliberate, documented scope limit; see this
    phase's write-up).
    """
    try:
        grading_scale = class_level.grading_scale
    except GradingScale.DoesNotExist:
        return None

    return grading_scale.bands.filter(
        min_percentage__lte=percentage, max_percentage__gte=percentage
    ).first()


def get_topics_for_subject(subject: Subject) -> QuerySet[Topic]:
    """
    All Topics under a single Subject, across every ClassLevel it's
    taught at. Powers the new "Curriculum" section on the Subject
    detail page, alongside the existing Assessment Components / Skill
    Checklist sections.
    """
    return subject.topics.select_related("class_level", "term")


def get_topics_for_level(class_level) -> dict[Subject, list[Topic]]:
    """
    All Topics for a single ClassLevel, grouped by Subject. Powers
    CurriculumOverviewView, which shows a level's whole syllabus across
    every subject in one place.

    Grouping is done HERE rather than in the view/template - this is a
    genuine query-shaping concern (which subjects exist for this level,
    in what order, with which topics under each), and selectors.py is
    where that kind of logic belongs per this project's established
    thin-views convention. A plain dict keyed by Subject instance is
    enough for template iteration (`{% for subject, topics in
    grouped.items %}`); no need for a dedicated dataclass at this scale.
    """
    topics = (
        Topic.objects.filter(class_level=class_level)
        .select_related("subject", "term")
        .order_by("subject__name", "order")
    )

    grouped: dict[Subject, list[Topic]] = {}
    for topic in topics:
        grouped.setdefault(topic.subject, []).append(topic)

    return grouped