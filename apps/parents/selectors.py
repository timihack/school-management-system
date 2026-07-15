from django.db.models import Q, QuerySet

from .models import Parent


def get_parent_list(*, search: str = "", is_active: bool | None = None) -> QuerySet[Parent]:
  qs = Parent.objects.select_related("user").prefetch_related("guardianships__student__user")

  if is_active is not None:
    qs = qs.filter(is_active=is_active)

  if search:
    qs = qs.filter(
      Q(user__first_name__icontains=search)
      | Q(user__last_name__icontains=search)
      | Q(user__username__icontains=search)
      | Q(user__email__icontains=search)
    )

  return qs


def get_children_for_parent(parent: Parent):
  """
  Powers the parent-role dashboard ("My Children"). This is the actual
  data-isolation boundary for the Parent role - not just a convenience
  query. RoleRequiredMixin proves a user IS a parent; this function is
  what guarantees they only ever see students THEY are linked to, never
  every student in the system. Getting this one query wrong would be a
  real data-leak, not a cosmetic bug.
  """
  from apps.students.models import Student

  return (
    Student.objects.filter(guardianships__parent=parent)
    .select_related("user")
    .distinct()
  )