from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from core.permissions.mixins import RoleRequiredMixin

from . import permissions, selectors, services
from .filters import ParentFilterParams
from .forms import GuardianshipCreateForm, ParentCreateForm, ParentUpdateForm
from .models import Guardianship, Parent
from .services import ParentCreateData


class ParentListView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_VIEW_PARENTS
    PAGE_SIZE = 10

    def get(self, request):
        filters = ParentFilterParams.from_request(request)
        parent_qs = selectors.get_parent_list(
            search=filters.search,
            is_active=filters.is_active_filter,
        )

        paginator = Paginator(parent_qs, self.PAGE_SIZE)
        page_obj = paginator.get_page(request.GET.get("page", 1))
        context = {"page_obj": page_obj, "filters": filters}

        if request.htmx:
            return render(request, "parents/partials/parent_table.html", context)

        return render(request, "parents/parent_list.html", context)


class ParentCreateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_PARENTS

    def get(self, request):
        return render(request, "parents/parent_form.html", {"form": ParentCreateForm()})

    def post(self, request):
        form = ParentCreateForm(request.POST)
        if not form.is_valid():
            return render(request, "parents/parent_form.html", {"form": form})

        data = ParentCreateData(**form.cleaned_data)
        parent, temporary_password = services.create_parent(data)

        messages.success(
            request,
            f"Parent '{parent}' created. Temporary password: {temporary_password} "
            "(shown once only - share it securely).",
        )
        return redirect("parents:detail", pk=parent.pk)


class ParentDetailView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_VIEW_PARENTS

    def get(self, request, pk):
        parent = get_object_or_404(selectors.get_parent_list(), pk=pk)
        guardianships = parent.guardianships.select_related("student__user")
        return render(
            request,
            "parents/parent_detail.html",
            {"parent": parent, "guardianships": guardianships},
        )


class ParentUpdateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_PARENTS

    def get(self, request, pk):
        parent = get_object_or_404(Parent, pk=pk)
        form = ParentUpdateForm(instance=parent)
        return render(request, "parents/parent_form.html", {"form": form, "parent": parent})

    def post(self, request, pk):
        parent = get_object_or_404(Parent, pk=pk)
        form = ParentUpdateForm(request.POST, instance=parent)
        if not form.is_valid():
            return render(
                request, "parents/parent_form.html", {"form": form, "parent": parent}
            )

        form.save()
        messages.success(request, "Parent updated.")
        return redirect("parents:detail", pk=parent.pk)


class ParentDeactivateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_DEACTIVATE_PARENTS

    def post(self, request, pk):
        parent = get_object_or_404(Parent, pk=pk)
        services.deactivate_parent(parent)

        if request.htmx:
            return render(
                request, "parents/partials/parent_status_badge.html", {"parent": parent}
            )

        messages.success(request, f"{parent} has been deactivated.")
        return redirect("parents:detail", pk=parent.pk)


class GuardianshipCreateView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_PARENTS

    def get(self, request, parent_pk):
        parent = get_object_or_404(Parent, pk=parent_pk)
        form = GuardianshipCreateForm(parent=parent)
        return render(
            request, "parents/guardianship_form.html", {"form": form, "parent": parent}
        )

    def post(self, request, parent_pk):
        parent = get_object_or_404(Parent, pk=parent_pk)
        form = GuardianshipCreateForm(request.POST, parent=parent)
        if not form.is_valid():
            return render(
                request, "parents/guardianship_form.html", {"form": form, "parent": parent}
            )

        services.link_guardianship(
            parent=parent,
            student=form.cleaned_data["student"],
            relationship=form.cleaned_data["relationship"],
            is_primary_contact=form.cleaned_data["is_primary_contact"],
            can_pickup=form.cleaned_data["can_pickup"],
        )
        messages.success(request, "Child linked to parent.")
        return redirect("parents:detail", pk=parent.pk)


class GuardianshipDeleteView(RoleRequiredMixin, View):
    allowed_roles = permissions.CAN_MANAGE_PARENTS

    def post(self, request, pk):
        guardianship = get_object_or_404(Guardianship, pk=pk)
        parent_pk = guardianship.parent_id
        services.unlink_guardianship(guardianship)
        messages.success(request, "Child unlinked from parent.")
        return redirect("parents:detail", pk=parent_pk)