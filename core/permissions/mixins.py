from django.core.exceptions import PermissionDenied

class RoleRequiredMixin:
    """
    Class-based view mixin restricting access to users whose `role`
    attribute is included in `allowed_roles`.
 
    This mixin deliberately does NOT check request.user.is_authenticated.
    That's already guaranteed project-wide by LoginRequiredMiddleware
    (see core/settings/base.py) before dispatch() ever runs here - so
    every future module (Students, Fees, Payroll, ...) only has to think
    about ROLE, never about whether the user is logged in at all.
 
    Usage:
        class PayrollListView(RoleRequiredMixin, ListView):
            allowed_roles = [User.Role.ADMIN, User.Role.STAFF]
            ...
    """
    allowed_roles: list[str] = []

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in self.allowed_roles:
            raise PermissionDenied('You do not have permission to access this page.')
        return super().dispatch(request, *args, **kwargs)