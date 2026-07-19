from django.db.models import Q, QuerySet

from .models import ClassArm, ClassEnrollment, ClassLevel


def get_class_level_list(*, search: str = "") -> QuerySet[ClassLevel]:
    qs = ClassLevel.objects.all()
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(category__icontains=search))
    return qs


def get_arms_for_level(class_level: ClassLevel) -> QuerySet[ClassArm]:
    return class_level.arms.select_related("class_teacher__user")


def get_current_enrollment(student) -> ClassEnrollment | None:
    """
    The single source of truth for "what class is this student in right
    now" - deliberately NOT cached on Student itself (no current-class
    FK there). Same reasoning as Guardianship's primary contact: one
    source of truth, queried, not duplicated and kept in sync by hand.
    """
    return (
        ClassEnrollment.objects.filter(student=student, is_current=True)
        .select_related("class_level", "class_arm")
        .first()
    )


def get_enrollment_history(student) -> QuerySet[ClassEnrollment]:
    return ClassEnrollment.objects.filter(student=student).select_related(
        "class_level", "class_arm"
    )


def get_repeat_count(student, class_level: ClassLevel) -> int:
    return ClassEnrollment.objects.filter(
        student=student, class_level=class_level, is_repeat=True
    ).count()


def get_current_students_in_arm(class_arm: ClassArm) -> QuerySet[ClassEnrollment]:
    return ClassEnrollment.objects.filter(class_arm=class_arm, is_current=True).select_related(
        "student__user"
    )