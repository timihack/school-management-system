import factory
from factory.django import DjangoModelFactory

from ..models import Department


class DepartmentFactory(DjangoModelFactory):
    class Meta:
        model = Department

    name = factory.Sequence(lambda n: f"Department {n}")
    description = "A school department."