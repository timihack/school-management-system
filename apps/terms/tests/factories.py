import datetime

import factory
from factory.django import DjangoModelFactory

from ..models import AcademicSession, Term


class AcademicSessionFactory(DjangoModelFactory):
    class Meta:
        model = AcademicSession
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"20{20+n}/20{21+n}")
    start_date = datetime.date(2024, 9, 1)
    end_date = datetime.date(2025, 7, 31)


class TermFactory(DjangoModelFactory):
    class Meta:
        model = Term

    academic_session = factory.SubFactory(AcademicSessionFactory)
    name = Term.TermName.FIRST
    sequence = 1
    start_date = datetime.date(2024, 9, 1)
    end_date = datetime.date(2024, 12, 15)