import datetime

import factory
from factory.django import DjangoModelFactory

from apps.accounts.models import User
from apps.accounts.tests.factories import UserFactory

from ..models import Staff


class StaffFactory(DjangoModelFactory):
    class Meta:
        model = Staff

    user = factory.SubFactory(UserFactory, role=User.Role.STAFF)
    employee_id = factory.Sequence(lambda n: f"STF{n:05d}")
    job_title = "Librarian"
    employment_type = Staff.EmploymentType.FULL_TIME
    date_of_birth = datetime.date(1988, 3, 20)
    date_joined = factory.LazyFunction(datetime.date.today)