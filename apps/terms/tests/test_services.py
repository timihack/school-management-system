import pytest

from apps.terms.models import Term
from apps.terms.selectors import get_current_session, get_current_term, is_last_term_of_session
from apps.terms.services import activate_term
from apps.terms.tests.factories import AcademicSessionFactory, TermFactory


@pytest.mark.django_db
class TestActivateTerm:
    def test_activating_a_term_marks_it_current(self):
        term = TermFactory()

        activate_term(term)
        term.refresh_from_db()

        assert term.is_current is True

    def test_activating_a_new_term_retires_the_previous_current_one(self):
        session = AcademicSessionFactory()
        first_term = TermFactory(academic_session=session, name=Term.TermName.FIRST, sequence=1)
        second_term = TermFactory(academic_session=session, name=Term.TermName.SECOND, sequence=2)

        activate_term(first_term)
        activate_term(second_term)

        first_term.refresh_from_db()
        second_term.refresh_from_db()
        assert first_term.is_current is False
        assert second_term.is_current is True
        assert Term.objects.filter(is_current=True).count() == 1

    def test_activation_is_global_across_different_sessions(self):
        """
        Confirms the constraint is genuinely global (no scoping field),
        unlike Guardianship/ClassEnrollment's per-student scoping -
        activating a term in a DIFFERENT session still retires whatever
        was current anywhere in the system.
        """
        term_in_session_a = TermFactory(academic_session=AcademicSessionFactory(name="2023/2024"))
        term_in_session_b = TermFactory(academic_session=AcademicSessionFactory(name="2024/2025"))

        activate_term(term_in_session_a)
        activate_term(term_in_session_b)

        term_in_session_a.refresh_from_db()
        assert term_in_session_a.is_current is False


@pytest.mark.django_db
class TestCurrentSessionDerivation:
    def test_no_current_term_means_no_current_session(self):
        TermFactory()  # exists, but never activated

        assert get_current_term() is None
        assert get_current_session() is None

    def test_current_session_is_derived_from_current_term(self):
        term = TermFactory()
        activate_term(term)

        assert get_current_session() == term.academic_session


@pytest.mark.django_db
class TestIsLastTermOfSession:
    def test_third_term_is_last(self):
        session = AcademicSessionFactory()
        TermFactory(academic_session=session, name=Term.TermName.FIRST, sequence=1)
        TermFactory(academic_session=session, name=Term.TermName.SECOND, sequence=2)
        third = TermFactory(academic_session=session, name=Term.TermName.THIRD, sequence=3)

        assert is_last_term_of_session(third) is True

    def test_first_term_is_not_last_when_later_terms_exist(self):
        session = AcademicSessionFactory()
        first = TermFactory(academic_session=session, name=Term.TermName.FIRST, sequence=1)
        TermFactory(academic_session=session, name=Term.TermName.SECOND, sequence=2)

        assert is_last_term_of_session(first) is False

    def test_a_lone_term_is_its_own_last_term(self):
        term = TermFactory(sequence=1)

        assert is_last_term_of_session(term) is True