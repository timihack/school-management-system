import datetime

import factory
from factory.django import DjangoModelFactory

from apps.accounts.models import User
from apps.accounts.tests.factories import UserFactory

from ..models import Student


class StudentFactory(DjangoModelFactory):
    class Meta:
        model = Student

    user = factory.SubFactory(UserFactory, role=User.Role.STUDENT)
    admission_number = factory.Sequence(lambda n: f"ADM{n:05d}")
    date_of_birth = datetime.date(2010, 1, 1)
    gender = Student.Gender.MALE
    admission_date = factory.LazyFunction(datetime.date.today)