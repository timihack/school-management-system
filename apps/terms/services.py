from django.db import transaction

from core.services import clear_current_flag

from .models import Term


@transaction.atomic
def activate_term(term: Term) -> Term:
    """
    Marks `term` as the current term, clearing whatever was current
    before it. Unlike link_guardianship/assign_student_to_class (which
    both clear-then-CREATE a brand new row), this clears-then-UPDATES an
    EXISTING row - a term is typically created ahead of time (e.g. an
    admin sets up "Second Term" before it starts) and activated as a
    separate action once it actually begins. This genuine shape
    difference is exactly why core.services.clear_current_flag only
    extracts the clearing half, leaving each caller to finish the "set
    the new one" half its own way.
    """
    clear_current_flag(Term, scope_filter={}, current_field="is_current", exclude_pk=term.pk)

    term.is_current = True
    term.save(update_fields=["is_current"])
    return term