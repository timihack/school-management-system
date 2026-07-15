import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory


@pytest.mark.django_db
def test_repeated_failed_logins_get_locked_out(client, settings):
    """
    Axes is disabled project-wide in core/settings/test.py (see that
    file's docstring for why). This test re-enables it JUST for itself,
    and deliberately uses real client.post() calls to the login view -
    never force_login() - since that's the actual code path Axes hooks
    into via AxesBackend.
    """
    settings.AXES_ENABLED = True
    settings.AXES_FAILURE_LIMIT = 3

    UserFactory(username="lockout_target", password="correct-horse-battery-staple")
    login_url = reverse("accounts:login")

    for _ in range(3):
        client.post(
            login_url, {"username": "lockout_target", "password": "wrong-password"}
        )

    # Correct password now - still locked out. Proves the block is on
    # ATTEMPT COUNT, not on whether the credentials happen to be right.
    response = client.post(
        login_url,
        {"username": "lockout_target", "password": "correct-horse-battery-staple"},
    )

    assert response.status_code == 429