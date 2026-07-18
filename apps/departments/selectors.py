from django.db.models import Q, QuerySet

from .models import Department


def get_department_list(*, search: str = "") -> QuerySet[Department]:
    qs = Department.objects.select_related("head_of_department")

    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))

    return qs