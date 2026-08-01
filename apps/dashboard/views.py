from django.shortcuts import render
from django.views.generic import TemplateView

from apps.accounts.models import User
from apps.attendance import selectors as attendance_selectors
from apps.parents import selectors as parent_selectors
from apps.parents.models import Parent
from apps.terms.selectors import get_current_term
from core.permissions.decorators import role_required
from core.permissions.mixins import RoleRequiredMixin


def home(request):
    """
    Branches by role for the first time. Admin/Staff/Teacher still see
    the shared placeholder dashboard - Parent gets a genuinely different
    page showing only THEIR OWN children, via
    parent_selectors.get_children_for_parent(), which is where the real
    data-isolation guarantee lives (see apps/parents/selectors.py).
    """
    if request.user.role == User.Role.PARENT:
        parent = Parent.objects.filter(user=request.user).first()
        children = parent_selectors.get_children_for_parent(parent) if parent else []

        current_term = get_current_term()
        children_with_attendance = [
            {
                "student": child,
                "attendance_summary": (
                    attendance_selectors.get_attendance_summary_for_student(child, current_term)
                    if current_term
                    else None
                ),
            }
            for child in children
        ]

        return render(
            request,
            "dashboard/parent_home.html",
            {"parent": parent, "children_with_attendance": children_with_attendance},
        )

    return render(request, "dashboard/home.html")


class AdminAreaView(RoleRequiredMixin, TemplateView):
    """
    Class-based RBAC example. This is the pattern to reach for whenever a
    module is naturally class-based - which most real modules (Students,
    Fees, Exams: ListView/DetailView/CreateView) will be.
    """

    template_name = "dashboard/admin_area.html"
    allowed_roles = [User.Role.ADMIN]


@role_required(User.Role.ADMIN, User.Role.STAFF)
def reports_preview(request):
    """
    Function-based RBAC example, and proof that role_required supports
    multiple allowed roles. Reach for this pattern for simple, one-off
    function views that don't warrant a full CBV.
    """
    return render(request, "dashboard/reports_preview.html")