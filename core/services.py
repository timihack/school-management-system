def clear_current_flag(
    model,
    *,
    scope_filter: dict,
    current_field: str = "is_current",
    exclude_pk=None,
) -> None:
    """
    Clears `current_field` on every row of `model` matching
    `scope_filter`. This is the shared half of the "at most one current
    X" pattern used across this project:

    - apps.parents.services.link_guardianship (is_primary_contact,
      scoped by student)
    - apps.classes.services.assign_student_to_class (is_current, scoped
      by student)
    - apps.terms.services.activate_term (is_current, scoped globally -
      an empty scope_filter)

    ADR-003 (docs/ARCHITECTURE_DECISIONS.md) predicted that a THIRD
    occurrence of this shape should trigger extracting a reusable piece
    instead of a fourth bespoke copy - this is that extraction, and both
    pre-existing implementations have been refactored to call it rather
    than keeping their own inline .update() calls.

    Deliberately only extracts the CLEARING half, not the "set the new
    one" half - the two existing call sites differ there in a way that
    doesn't collapse cleanly: link_guardianship and
    assign_student_to_class both CREATE a new row with the flag already
    set, while activate_term needs to SET the flag on an EXISTING row.
    Trying to force both shapes through one generic function would need
    more parameters and branching than just leaving that half to each
    caller, who already knows which shape it needs.
    """
    qs = model.objects.filter(**scope_filter, **{current_field: True})
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    qs.update(**{current_field: False})