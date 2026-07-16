import datetime

import factory
from factory.django import DjangoModelFactory

from apps.accounts.models import User
from apps.accounts.tests.factories import UserFactory

from ..models import Teacher


class TeacherFactory(DjangoModelFactory):
    class Meta:
        model = Teacher

    user = factory.SubFactory(UserFactory, role=User.Role.TEACHER)
    employee_id = factory.Sequence(lambda n: f"EMP{n:05d}")
    qualification = "B.Ed"
    date_of_birth = datetime.date(1985, 6, 15)
    date_joined = factory.LazyFunction(datetime.date.today)