import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.tests.factories import UserFactory
from apps.terms.models import AcademicSession, Term
from apps.terms.tests.factories import AcademicSessionFactory, TermFactory


@pytest.mark.django_db
class TestAcademicSessionListView:
    def test_admin_can_view(self, client):
        admin = UserFactory(username="admin_term1", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)

        response = client.get(reverse("terms:session_list"))

        assert response.status_code == 200

    def test_student_is_forbidden(self, client):
        student = UserFactory(username="student_term1", password="pass12345", role=User.Role.STUDENT)
        client.force_login(student)

        response = client.get(reverse("terms:session_list"))

        assert response.status_code == 403


@pytest.mark.django_db
class TestAcademicSessionCreateView:
    def test_admin_can_create_session(self, client):
        admin = UserFactory(username="admin_term2", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)

        response = client.post(
            reverse("terms:session_create"),
            {"name": "2025/2026", "start_date": "2025-09-01", "end_date": "2026-07-31"},
        )

        assert response.status_code == 302
        assert AcademicSession.objects.filter(name="2025/2026").exists()

    def test_staff_cannot_create_session(self, client):
        staff = UserFactory(username="staff_term1", password="pass12345", role=User.Role.STAFF)
        client.force_login(staff)

        response = client.get(reverse("terms:session_create"))

        assert response.status_code == 403


@pytest.mark.django_db
class TestTermCreateView:
    def test_admin_can_create_term_within_session_dates(self, client):
        admin = UserFactory(username="admin_term3", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        session = AcademicSessionFactory()

        response = client.post(
            reverse("terms:term_create", args=[session.pk]),
            {
                "name": "FIRST",
                "sequence": 1,
                "start_date": "2024-09-01",
                "end_date": "2024-12-15",
                "next_term_begins": "2025-01-06",
                "total_school_days": 80,
            },
        )

        assert response.status_code == 302
        assert Term.objects.filter(academic_session=session, name="FIRST").exists()

    def test_term_dates_outside_session_are_rejected(self, client):
        admin = UserFactory(username="admin_term4", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        session = AcademicSessionFactory()  # 2024-09-01 to 2025-07-31

        response = client.post(
            reverse("terms:term_create", args=[session.pk]),
            {
                "name": "FIRST",
                "sequence": 1,
                "start_date": "2024-01-01",  # before session starts
                "end_date": "2024-12-15",
                "next_term_begins": "",
                "total_school_days": "",
            },
        )

        assert response.status_code == 200
        assert b"cannot start before" in response.content


@pytest.mark.django_db
class TestTermActivateView:
    def test_admin_can_activate_a_term(self, client):
        admin = UserFactory(username="admin_term5", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        term = TermFactory()

        response = client.post(reverse("terms:term_activate", args=[term.pk]))

        term.refresh_from_db()
        assert response.status_code == 302
        assert term.is_current is True

    def test_teacher_cannot_activate_a_term(self, client):
        teacher = UserFactory(username="teacher_term1", password="pass12345", role=User.Role.TEACHER)
        client.force_login(teacher)
        term = TermFactory()

        response = client.post(reverse("terms:term_activate", args=[term.pk]))

        assert response.status_code == 403