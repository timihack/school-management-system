from .models import AcademicSession, Term


def get_current_term() -> Term | None:
    return Term.objects.select_related("academic_session").filter(is_current=True).first()


def get_current_session() -> AcademicSession | None:
    """
    Derived from the current term, never stored independently - see
    models.py's Term docstring for why. Returns None if no term has been
    activated yet (a perfectly valid state, e.g. right after this app is
    first deployed).
    """
    current_term = get_current_term()
    return current_term.academic_session if current_term else None


def get_terms_for_session(session: AcademicSession):
    return session.terms.all()


def is_last_term_of_session(term: Term) -> bool:
    """
    Whether `term` is the final term of its session - e.g. Third Term in
    a standard 3-term year. Computed, not stored, so it never needs
    updating if a school adds or removes a term from a session later.
    The future Examinations phase will use this to decide whether the
    Promote action should even be reachable for a given term, per
    docs/ACADEMIC_STRUCTURE_REQUIREMENTS.md Section 3 ("Third Term is
    when promotion to next class takes place").
    """
    return not term.academic_session.terms.filter(sequence__gt=term.sequence).exists()