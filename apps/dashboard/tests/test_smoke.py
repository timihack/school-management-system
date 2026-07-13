import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_home_page_loads(client):
    response = client.get(reverse("dashboard:home"))
    assert response.status_code == 200
    assert b"Foundation is live" in response.content