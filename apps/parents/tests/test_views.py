import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.tests.factories import UserFactory
from apps.parents.models import Guardianship
from apps.parents.tests.factories import GuardianshipFactory, ParentFactory
from apps.students.tests.factories import StudentFactory


@pytest.mark.django_db
class TestParentListView:
    def test_admin_can_view_list(self, client):
        admin = UserFactory(username="admin_p1", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)

        response = client.get(reverse("parents:list"))

        assert response.status_code == 200

    def test_parent_role_is_forbidden(self, client):
        parent_user = UserFactory(
            username="parent_p1", password="pass12345", role=User.Role.PARENT
        )
        client.force_login(parent_user)

        response = client.get(reverse("parents:list"))

        assert response.status_code == 403


@pytest.mark.django_db
class TestParentCreateView:
    def test_admin_can_create_parent(self, client):
        admin = UserFactory(username="admin_p2", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)

        response = client.post(
            reverse("parents:create"),
            {
                "first_name": "Mary",
                "last_name": "Smith",
                "email": "mary.smith@example.com",
                "occupation": "Nurse",
                "phone_number": "",
                "address": "",
            },
        )

        assert response.status_code == 302
        assert User.objects.filter(email="mary.smith@example.com", role=User.Role.PARENT).exists()


@pytest.mark.django_db
class TestGuardianshipLinking:
    def test_admin_can_link_existing_student_by_admission_number(self, client):
        admin = UserFactory(username="admin_p3", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        parent = ParentFactory()
        student = StudentFactory(admission_number="ADM00777")

        response = client.post(
            reverse("parents:link_child", args=[parent.pk]),
            {
                "student_admission_number": "ADM00777",
                "relationship": "MOTHER",
                "is_primary_contact": "on",
                "can_pickup": "on",
            },
        )

        assert response.status_code == 302
        assert Guardianship.objects.filter(parent=parent, student=student).exists()

    def test_unknown_admission_number_is_rejected(self, client):
        admin = UserFactory(username="admin_p4", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        parent = ParentFactory()

        response = client.post(
            reverse("parents:link_child", args=[parent.pk]),
            {
                "student_admission_number": "NOPE",
                "relationship": "MOTHER",
            },
        )

        assert response.status_code == 200
        assert b"No student found" in response.content

    def test_duplicate_link_is_rejected(self, client):
        admin = UserFactory(username="admin_p5", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        guardianship = GuardianshipFactory()

        response = client.post(
            reverse("parents:link_child", args=[guardianship.parent.pk]),
            {
                "student_admission_number": guardianship.student.admission_number,
                "relationship": "FATHER",
            },
        )

        assert response.status_code == 200
        assert b"already linked" in response.content

    def test_unlink_removes_the_guardianship(self, client):
        admin = UserFactory(username="admin_p6", password="pass12345", role=User.Role.ADMIN)
        client.force_login(admin)
        guardianship = GuardianshipFactory()

        response = client.post(reverse("parents:unlink_child", args=[guardianship.pk]))

        assert response.status_code == 302
        assert not Guardianship.objects.filter(pk=guardianship.pk).exists()