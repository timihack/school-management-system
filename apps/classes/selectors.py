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


def get_current_students_in_arm(class_arm: ClassArm) -> QuerySet:
    """
    Returns the actual Student queryset for whoever is currently
    enrolled in this arm.

    CORRECTED in the Attendance no-arm-support patch: this previously
    returned the ClassEnrollment rows themselves (QuerySet[ClassEnrollment])
    despite its name promising Students - the one real caller
    (apps.attendance) treated each row's .pk as if it were the STUDENT's
    pk, when it was actually the ClassEnrollment row's own pk. That's
    exactly the kind of bug that only surfaces once something depends on
    the return type meaning what its name says - fixed here at the
    source rather than patched around in the caller.
    """
    from apps.students.models import Student

    student_ids = ClassEnrollment.objects.filter(
        class_arm=class_arm, is_current=True
    ).values_list("student_id", flat=True)
    return Student.objects.filter(pk__in=student_ids).select_related("user")


def get_current_students_in_level(class_level: ClassLevel) -> QuerySet:
    """
    The no-arm equivalent of get_current_students_in_arm: students
    currently enrolled DIRECTLY at this level (class_arm is NULL on
    their enrollment) - this is the roster for a level where
    has_arms=False, mirroring exactly how ClassEnrollment itself already
    represents "enrolled at a level with no arm" as class_arm=None
    rather than some fabricated placeholder arm.
    """
    from apps.students.models import Student

    student_ids = ClassEnrollment.objects.filter(
        class_level=class_level, class_arm__isnull=True, is_current=True
    ).values_list("student_id", flat=True)
    return Student.objects.filter(pk__in=student_ids).select_related("user")