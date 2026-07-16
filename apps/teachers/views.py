from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.accounts.models import User
from core.permissions.mixins import RoleRequiredMixin

from . import permissions, selectors, services
from .filters import TeacherFilterParams
from .forms import TeacherCreateForm, TeacherUpdateForm
from .models import Teacher
from .services import TeacherCreateData


class TeacherListView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_VIEW_TEACHERS
    PAGE_SIZE = 10

    def get(self, request):
        filters = TeacherFilterParams.from_request(request)
        teacher_qs = selectors.get_teacher_list(
            search=filters.search,
            is_active=filters.is_active_filter,
        )

        paginator = Paginator(teacher_qs, self.PAGE_SIZE)
        page_obj = paginator.get_page(request.GET.get("page", 1))
        context = {"page_obj": page_obj, "filters": filters}

        if request.htmx:
            return render(request, "teachers/partials/teacher_table.html", context)

        return render(request, "teachers/teacher_list.html", context)


class TeacherCreateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_TEACHERS

    def get(self, request):
        return render(request, "teachers/teacher_form.html", {"form": TeacherCreateForm()})

    def post(self, request):
        form = TeacherCreateForm(request.POST)
        if not form.is_valid():
            return render(request, "teachers/teacher_form.html", {"form": form})

        data = TeacherCreateData(**form.cleaned_data)
        teacher, temporary_password = services.create_teacher(data)

        messages.success(
            request,
            f"Teacher '{teacher}' created. Temporary password: {temporary_password} "
            "(shown once only - share it securely).",
        )
        return redirect("teachers:detail", pk=teacher.pk)


class TeacherDetailView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_VIEW_TEACHERS

    def get(self, request, pk):
        teacher = get_object_or_404(selectors.get_teacher_list(), pk=pk)
        return render(request, "teachers/teacher_detail.html", {"teacher": teacher})


class TeacherUpdateView(RoleRequiredMixin, View):
    """
    Role-gated to Admin/Staff/Teacher - broader than CAN_MANAGE_TEACHERS
    on purpose, because a Teacher IS allowed here, just not for just
    anyone's record. This is the project's first OBJECT-level check:
    RoleRequiredMixin proves "you're some kind of Teacher/Staff/Admin,"
    but only _get_teacher_or_403() below proves "you're allowed to touch
    THIS SPECIFIC Teacher row." A Staff/Admin can edit anyone; a Teacher
    can only edit themselves - the two checks answer genuinely different
    questions and this view uses both.

    This closes the object-level-permissions gap in docs/SECURITY.md for
    ONE case, not generally - a reusable OwnerOrRoleRequiredMixin is
    worth building once a second or third case exists to design it
    against, same reasoning as the deferred Teacher/Staff base model.
    """

    allowed_roles = permissions.CAN_MANAGE_TEACHERS + [User.Role.TEACHER]

    def _get_teacher_or_403(self, request, pk) -> Teacher:
        teacher = get_object_or_404(Teacher, pk=pk)
        is_manager = request.user.role in permissions.CAN_MANAGE_TEACHERS
        is_self = teacher.user_id == request.user.id
        if not (is_manager or is_self):
            raise PermissionDenied("You can only edit your own profile.")
        return teacher

    def get(self, request, pk):
        teacher = self._get_teacher_or_403(request, pk)
        form = TeacherUpdateForm(instance=teacher)
        return render(
            request, "teachers/teacher_form.html", {"form": form, "teacher": teacher}
        )

    def post(self, request, pk):
        teacher = self._get_teacher_or_403(request, pk)
        form = TeacherUpdateForm(request.POST, instance=teacher)
        if not form.is_valid():
            return render(
                request, "teachers/teacher_form.html", {"form": form, "teacher": teacher}
            )

        form.save()
        messages.success(request, "Profile updated.")
        return redirect("teachers:detail", pk=teacher.pk)


class TeacherDeactivateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_DEACTIVATE_TEACHERS

    def post(self, request, pk):
        teacher = get_object_or_404(Teacher, pk=pk)
        services.deactivate_teacher(teacher)

        if request.htmx:
            return render(
                request, "teachers/partials/teacher_status_badge.html", {"teacher": teacher}
            )

        messages.success(request, f"{teacher} has been deactivated.")
        return redirect("teachers:detail", pk=teacher.pk)