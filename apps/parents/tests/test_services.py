import pytest

from apps.accounts.models import User
from apps.parents.models import Guardianship
from apps.parents.services import (
    ParentCreateData,
    create_parent,
    deactivate_parent,
    link_guardianship,
    unlink_guardianship,
)
from apps.parents.tests.factories import GuardianshipFactory, ParentFactory
from apps.students.tests.factories import StudentFactory


@pytest.mark.django_db
class TestCreateParent:
    def test_creates_linked_user_and_parent(self):
        data = ParentCreateData(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            occupation="Accountant",
        )

        parent, temporary_password = create_parent(data)

        assert parent.pk is not None
        assert parent.user.role == User.Role.PARENT
        assert parent.user.check_password(temporary_password)


@pytest.mark.django_db
class TestDeactivateParent:
    def test_deactivates_parent_and_disables_login(self):
        parent = ParentFactory()

        deactivate_parent(parent)
        parent.refresh_from_db()
        parent.user.refresh_from_db()

        assert parent.is_active is False
        assert parent.user.is_active is False


@pytest.mark.django_db
class TestLinkGuardianship:
    def test_creates_link(self):
        parent = ParentFactory()
        student = StudentFactory()

        guardianship = link_guardianship(
            parent=parent, student=student, relationship=Guardianship.Relationship.MOTHER
        )

        assert guardianship.parent == parent
        assert guardianship.student == student

    def test_new_primary_contact_clears_previous_one(self):
        student = StudentFactory()
        first_guardianship = GuardianshipFactory(student=student, is_primary_contact=True)
        second_parent = ParentFactory()

        link_guardianship(
            parent=second_parent,
            student=student,
            relationship=Guardianship.Relationship.MOTHER,
            is_primary_contact=True,
        )

        first_guardianship.refresh_from_db()
        assert first_guardianship.is_primary_contact is False


@pytest.mark.django_db
class TestUnlinkGuardianship:
    def test_removes_the_link(self):
        guardianship = GuardianshipFactory()
        guardianship_pk = guardianship.pk

        unlink_guardianship(guardianship)

        assert not Guardianship.objects.filter(pk=guardianship_pk).exists()