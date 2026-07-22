from django.db import transaction

from apps.terms.selectors import get_current_session
from core.services import clear_current_flag

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
    academic_session=None,
) -> ClassEnrollment:
    """
    Creates a new CURRENT enrollment, retiring whatever was current
    before it - now via the shared core.services.clear_current_flag
    utility (Phase 10's ADR-003 extraction) rather than a bespoke
    .filter().update() line.

    academic_session defaults to the CURRENT session (via
    apps.terms.selectors.get_current_session) if not explicitly passed -
    same precedent as Phase 7, where apps.teachers/apps.staff forms
    imported apps.departments directly to wire up their deferred FK.
    Terms is a genuinely foundational, cross-cutting concept (like
    accounts.User) that many future apps will need to reference
    regardless of build order, not a narrow domain entity - see this
    phase's write-up for the full reasoning. A top-level import is used
    here (not a local one) for that same consistency with precedent -
    there's no circular dependency risk since apps.terms never imports
    apps.classes.
    """
    clear_current_flag(ClassEnrollment, scope_filter={"student": student}, current_field="is_current")

    return ClassEnrollment.objects.create(
        student=student,
        class_level=class_level,
        class_arm=class_arm,
        is_current=True,
        is_repeat=is_repeat,
        assigned_by=assigned_by,
        academic_session=academic_session or get_current_session(),
    )