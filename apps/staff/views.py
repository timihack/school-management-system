from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.accounts.models import User
from core.permissions.mixins import RoleRequiredMixin

from . import permissions, selectors, services
from .filters import StaffFilterParams
from .forms import StaffCreateForm, StaffUpdateForm
from .models import Staff
from .services import StaffCreateData


class StaffListView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_VIEW_STAFF
    PAGE_SIZE = 10

    def get(self, request):
        filters = StaffFilterParams.from_request(request)
        staff_qs = selectors.get_staff_list(
            search=filters.search,
            is_active=filters.is_active_filter,
        )

        paginator = Paginator(staff_qs, self.PAGE_SIZE)
        page_obj = paginator.get_page(request.GET.get("page", 1))
        context = {"page_obj": page_obj, "filters": filters}

        if request.htmx:
            return render(request, "staff/partials/staff_table.html", context)

        return render(request, "staff/staff_list.html", context)


class StaffCreateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_STAFF

    def get(self, request):
        return render(request, "staff/staff_form.html", {"form": StaffCreateForm()})

    def post(self, request):
        form = StaffCreateForm(request.POST)
        if not form.is_valid():
            return render(request, "staff/staff_form.html", {"form": form})

        data = StaffCreateData(**form.cleaned_data)
        staff, temporary_password = services.create_staff(data)

        messages.success(
            request,
            f"Staff member '{staff}' created. Temporary password: {temporary_password} "
            "(shown once only - share it securely).",
        )
        return redirect("staff:detail", pk=staff.pk)


class StaffDetailView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_VIEW_STAFF

    def get(self, request, pk):
        staff = get_object_or_404(selectors.get_staff_list(), pk=pk)
        return render(request, "staff/staff_detail.html", {"staff": staff})


class StaffUpdateView(RoleRequiredMixin, View):
    """
    CASE #2 of the object-level self-edit pattern (Teacher, Phase 5, was
    case #1). allowed_roles broadens to admit STAFF at the role-gate
    level - but unlike Teacher, CAN_MANAGE_STAFF is ADMIN-only, so this
    broadening is the ONLY way a staff member reaches this view at all.
    The object-level check below then restricts them to their own
    record. Per the note left in docs/SECURITY.md after Phase 5: this is
    still copy-paste, not yet a reusable mixin - that's worth doing once
    a third case shows up.
    """

    allowed_roles = permissions.CAN_MANAGE_STAFF + [User.Role.STAFF]

    def _get_staff_or_403(self, request, pk) -> Staff:
        staff = get_object_or_404(Staff, pk=pk)
        is_manager = request.user.role in permissions.CAN_MANAGE_STAFF
        is_self = staff.user_id == request.user.id
        if not (is_manager or is_self):
            raise PermissionDenied("You can only edit your own profile.")
        return staff

    def get(self, request, pk):
        staff = self._get_staff_or_403(request, pk)
        form = StaffUpdateForm(instance=staff)
        return render(request, "staff/staff_form.html", {"form": form, "staff": staff})

    def post(self, request, pk):
        staff = self._get_staff_or_403(request, pk)
        form = StaffUpdateForm(request.POST, instance=staff)
        if not form.is_valid():
            return render(request, "staff/staff_form.html", {"form": form, "staff": staff})

        form.save()
        messages.success(request, "Profile updated.")
        return redirect("staff:detail", pk=staff.pk)


class StaffDeactivateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_DEACTIVATE_STAFF

    def post(self, request, pk):
        staff = get_object_or_404(Staff, pk=pk)
        services.deactivate_staff(staff)

        if request.htmx:
            return render(
                request, "staff/partials/staff_status_badge.html", {"staff": staff}
            )

        messages.success(request, f"{staff} has been deactivated.")
        return redirect("staff:detail", pk=staff.pk)