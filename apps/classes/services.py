from django.db import transaction

from .models import ClassEnrollment, ClassLevel, PromotionPolicy


def ensure_promotion_policy_exists(class_level: ClassLevel) -> PromotionPolicy:
    """
    Called right after a ClassLevel is created, so editing a policy in
    the UI is always an UPDATE, never a create-from-scratch. Uses
    get_or_create rather than a signal - keeps the side effect explicit
    and visible at the call site, consistent with this project's
    preference against signals.py unless a genuine cross-cutting hook is
    needed (none is, here - there's exactly one place a ClassLevel gets
    created).
    """
    policy, _ = PromotionPolicy.objects.get_or_create(class_level=class_level)
    return policy


@transaction.atomic
def assign_student_to_class(
    *,
    student,
    class_level: ClassLevel,
    class_arm=None,
    assigned_by=None,
    is_repeat: bool = False,
) -> ClassEnrollment:
    """
    Creates a new CURRENT enrollment, retiring whatever was current
    before it. Mirrors apps.parents.services.link_guardianship()'s
    "clear the old flag before inserting the new one" pattern exactly -
    the conditional UniqueConstraint on ClassEnrollment would otherwise
    reject this insert outright.
    """
    ClassEnrollment.objects.filter(student=student, is_current=True).update(is_current=False)

    return ClassEnrollment.objects.create(
        student=student,
        class_level=class_level,
        class_arm=class_arm,
        is_current=True,
        is_repeat=is_repeat,
        assigned_by=assigned_by,
    )