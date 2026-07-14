from functools import wraps
from django.core.exceptions import PermissionDenied


def role_required(*allowed_roles):
  """
  Function-based view decorator restricting access to users whose
  `role` is one of `allowed_roles`.

  Same assumption as RoleRequiredMixin: LoginRequiredMiddleware has
  already guaranteed request.user is authenticated by the time this
  decorator runs, so it only needs to check role.

  Usage:
      @role_required(User.Role.ADMIN, User.Role.STAFF)
      def payroll_list(request):
          ...
  """
  def decorator(view_func):
      @wraps(view_func)
      def _wrapped_view(request, *args, **kwargs):
          if request.user.role not in allowed_roles:
              raise PermissionDenied('You do not have access this page.')
          return view_func(request, *args, **kwargs)
      return _wrapped_view
  return decorator
