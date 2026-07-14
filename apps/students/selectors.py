from django.db.models import Q, QuerySet

from .models import Student


def get_student_list(*, search: str = "", is_active: bool | None = None) -> QuerySet[Student]:
    """
    Read-only query builder for the student list page. Kept separate
    from the view so the same filtering logic can be reused later (CSV
    export, a "my students" widget on a teacher's dashboard, etc.)
    without duplicating query logic inside a view.
    """
    qs = Student.objects.select_related("user")

    if is_active is not None:
        qs = qs.filter(is_active=is_active)

    if search:
        qs = qs.filter(
            Q(admission_number__icontains=search)
            | Q(user__first_name__icontains=search)
            | Q(user__last_name__icontains=search)
            | Q(user__username__icontains=search)
        )

    return qs