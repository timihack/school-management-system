import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory


@pytest.mark.django_db
def test_home_page_redirects_anonymous_user_to_login(client):
    """
    Behavior CHANGED in Phase 2: before LoginRequiredMiddleware existed,
    this returned 200 for anyone. Now every view requires auth by
    default, so an anonymous request must be redirected to login instead.
    """
    response = client.get(reverse("dashboard:home"))
    assert response.status_code == 302
    assert reverse("accounts:login") in response.url


@pytest.mark.django_db
def test_home_page_loads_for_authenticated_user(client):
    user = UserFactory(username="dave", password="testpass123")
    client.force_login(user)

    response = client.get(reverse("dashboard:home"))

    assert response.status_code == 200
    assert b"Foundation is live" in response.content