from django.db.models import Q, QuerySet

from .models import Staff


def get_staff_list(*, search: str = "", is_active: bool | None = None) -> QuerySet[Staff]:
    qs = Staff.objects.select_related("user")

    if is_active is not None:
        qs = qs.filter(is_active=is_active)

    if search:
        qs = qs.filter(
            Q(employee_id__icontains=search)
            | Q(job_title__icontains=search)
            | Q(user__first_name__icontains=search)
            | Q(user__last_name__icontains=search)
            | Q(user__username__icontains=search)
        )

    return qs