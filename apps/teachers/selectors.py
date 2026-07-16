from django.db.models import Q, QuerySet

from .models import Teacher


def get_teacher_list(*, search: str = "", is_active: bool | None = None) -> QuerySet[Teacher]:
    qs = Teacher.objects.select_related("user")

    if is_active is not None:
        qs = qs.filter(is_active=is_active)

    if search:
        qs = qs.filter(
            Q(employee_id__icontains=search)
            | Q(qualification__icontains=search)
            | Q(user__first_name__icontains=search)
            | Q(user__last_name__icontains=search)
            | Q(user__username__icontains=search)
        )

    return qs