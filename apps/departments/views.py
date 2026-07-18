from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from core.permissions.mixins import RoleRequiredMixin

from . import permissions, selectors, services
from .filters import DepartmentFilterParams
from .forms import DepartmentForm
from .models import Department


class DepartmentListView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_VIEW_DEPARTMENTS
    PAGE_SIZE = 10

    def get(self, request):
        filters = DepartmentFilterParams.from_request(request)
        department_qs = selectors.get_department_list(search=filters.search)

        paginator = Paginator(department_qs, self.PAGE_SIZE)
        page_obj = paginator.get_page(request.GET.get("page", 1))
        context = {"page_obj": page_obj, "filters": filters}

        if request.htmx:
            return render(request, "departments/partials/department_table.html", context)

        return render(request, "departments/department_list.html", context)


class DepartmentCreateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_DEPARTMENTS

    def get(self, request):
        return render(request, "departments/department_form.html", {"form": DepartmentForm()})

    def post(self, request):
        form = DepartmentForm(request.POST)
        if not form.is_valid():
            return render(request, "departments/department_form.html", {"form": form})

        department = form.save()
        messages.success(request, f"Department '{department}' created.")
        return redirect("departments:detail", pk=department.pk)


class DepartmentDetailView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_VIEW_DEPARTMENTS

    def get(self, request, pk):
        department = get_object_or_404(selectors.get_department_list(), pk=pk)
        teachers = department.teacher_set.select_related("user")
        staff_members = department.staff_set.select_related("user")
        return render(
            request,
            "departments/department_detail.html",
            {"department": department, "teachers": teachers, "staff_members": staff_members},
        )


class DepartmentUpdateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_DEPARTMENTS

    def get(self, request, pk):
        department = get_object_or_404(Department, pk=pk)
        form = DepartmentForm(instance=department)
        return render(
            request, "departments/department_form.html", {"form": form, "department": department}
        )

    def post(self, request, pk):
        department = get_object_or_404(Department, pk=pk)
        form = DepartmentForm(request.POST, instance=department)
        if not form.is_valid():
            return render(
                request,
                "departments/department_form.html",
                {"form": form, "department": department},
            )

        form.save()
        messages.success(request, "Department updated.")
        return redirect("departments:detail", pk=department.pk)


class DepartmentDeleteView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_DEPARTMENTS

    def post(self, request, pk):
        department = get_object_or_404(Department, pk=pk)
        name = str(department)
        result = services.delete_department(department)

        messages.success(
            request,
            f"'{name}' deleted. {result['teacher_count']} teacher(s) and "
            f"{result['staff_count']} staff member(s) were unassigned.",
        )
        return redirect("departments:list")