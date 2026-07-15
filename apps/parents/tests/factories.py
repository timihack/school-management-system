import factory
from factory.django import DjangoModelFactory

from apps.accounts.models import User
from apps.accounts.tests.factories import UserFactory
from apps.students.tests.factories import StudentFactory

from ..models import Guardianship, Parent


class ParentFactory(DjangoModelFactory):
    class Meta:
        model = Parent

    user = factory.SubFactory(UserFactory, role=User.Role.PARENT)
    occupation = "Engineer"


class GuardianshipFactory(DjangoModelFactory):
    class Meta:
        model = Guardianship

    parent = factory.SubFactory(ParentFactory)
    student = factory.SubFactory(StudentFactory)
    relationship = Guardianship.Relationship.FATHER
    is_primary_contact = True
    can_pickup = True