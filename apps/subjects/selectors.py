from django.db.models import Q, QuerySet

from .models import GradeBand, GradingScale, Subject


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