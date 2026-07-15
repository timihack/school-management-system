import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.tests.factories import UserFactory
from apps.parents.tests.factories import GuardianshipFactory


@pytest.mark.django_db
class TestParentDashboard:
    def test_parent_sees_only_their_own_children(self, client):
        guardianship_a = GuardianshipFactory()
        guardianship_b = GuardianshipFactory()

        client.force_login(guardianship_a.parent.user)
        response = client.get(reverse("dashboard:home"))

        assert response.status_code == 200
        assert guardianship_a.student.admission_number.encode() in response.content
        assert guardianship_b.student.admission_number.encode() not in response.content

    def test_parent_without_profile_sees_friendly_message(self, client):
        parent_user = UserFactory(
            username="orphan_parent", password="pass12345", role=User.Role.PARENT
        )
        client.force_login(parent_user)

        response = client.get(reverse("dashboard:home"))

        assert response.status_code == 200
        assert b"contact the school office" in response.content

    def test_non_parent_roles_see_the_generic_dashboard(self, client):
        admin = UserFactory(username="admin_dash", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)

        response = client.get(reverse("dashboard:home"))

        assert response.status_code == 200
        assert b"Foundation is live" in response.content