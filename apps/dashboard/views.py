from django.shortcuts import render
from django.views.generic import TemplateView

from apps.accounts.models import User
from core.permissions.decorators import role_required
from core.permissions.mixins import RoleRequiredMixin


def home(request):
    """
    Shared landing page for every authenticated role right now. Per-role
    dashboards (distinct widgets for admin vs teacher vs student) will
    replace this view in later phases as each domain module gets built -
    for now, everyone lands here after login.
    """
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