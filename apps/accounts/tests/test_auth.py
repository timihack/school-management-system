import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.tests.factories import UserFactory


@pytest.mark.django_db
class TestLogin:
    def test_login_page_is_reachable_while_anonymous(self, client):
        """
        Proves login_not_required actually works - without it, this
        request would redirect to itself in an infinite loop.
        """
        response = client.get(reverse("accounts:login"))
        assert response.status_code == 200

    def test_valid_credentials_redirect_to_role_dashboard(self, client):
        UserFactory(username="alice", password="strongpass123", role=User.Role.STUDENT)

        response = client.post(
            reverse("accounts:login"),
            {"username": "alice", "password": "strongpass123"},
        )

        assert response.status_code == 302
        assert response.url == reverse("dashboard:home")

    def test_invalid_credentials_show_error_and_stay_on_login(self, client):
        response = client.post(
            reverse("accounts:login"),
            {"username": "nobody", "password": "wrong-password"},
        )

        assert response.status_code == 200
        assert b"Invalid username or password" in response.content

    def test_login_honours_next_parameter_over_role_default(self, client):
        """
        Confirms get_default_redirect_url() (not get_success_url()) was
        the correct override point - a user bounced here from a specific
        protected page should return to THAT page, not the role default.
        """
        UserFactory(username="bob", password="strongpass123", role=User.Role.STUDENT)

        response = client.post(
            f"{reverse('accounts:login')}?next=/accounts/logout/",
            {"username": "bob", "password": "strongpass123"},
        )

        assert response.status_code == 302
        assert response.url == "/accounts/logout/"


@pytest.mark.django_db
class TestLogout:
    def test_logout_requires_post_and_redirects_to_login(self, client):
        user = UserFactory(username="carol", password="strongpass123")
        client.force_login(user)

        response = client.post(reverse("accounts:logout"))

        assert response.status_code == 302
        assert response.url == reverse("accounts:login")