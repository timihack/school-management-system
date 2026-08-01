from django.core.exceptions import PermissionDenied


def check_role_or_owner(*, request, allowed_roles: list[str], is_owner: bool) -> None:
    """
    Shared check for "role-level access OR object-level ownership, else
    403" - the pattern behind Teacher's self-edit (Phase 5), Staff's
    self-edit (Phase 6), and now Attendance's "class teacher of this
    specific arm" check (Phase 11). docs/SECURITY.md explicitly flagged
    that a THIRD occurrence should get this reusable function instead of
    a third copy-paste - this is that extraction, and both pre-existing
    implementations (apps/teachers/views.py, apps/staff/views.py) have
    been refactored to call it.

    Deliberately a plain function, not a dispatch-level mixin with an
    auto-fetched object: the three real call sites reach their object
    differently enough (a Teacher pk, a Staff pk, a ClassArm reached via
    a query parameter with a fallback to "the requester's own arm") that
    a generic get_object()-based mixin would need about as much
    per-view configuration as just calling this function directly inside
    each view's own get()/post() - for no real reduction in code. Same
    reasoning as core/services.py::clear_current_flag only extracting
    the half that's genuinely identical everywhere.
    """
    if request.user.role in allowed_roles:
        return
    if is_owner:
        return
    raise PermissionDenied("You do not have access to this resource.")