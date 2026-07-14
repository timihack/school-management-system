from django.contrib.auth.views import LoginView
from django.shortcuts import resolve_url

from .forms import StyledAuthenticationForm
from .models import User


class RoleBasedLoginView(LoginView):
  """
  Authenticates via Django's built-in session auth (unchanged), then
  routes the user to a role-appropriate landing page.

  IMPORTANT: this overrides get_default_redirect_url(), NOT
  get_success_url(). LoginView.get_success_url() (inherited, untouched)
  already does `return self.get_redirect_url() or self.get_default_redirect_url()`
  - i.e. it first honours a safe `?next=` parameter (e.g. someone who
  was bounced here from a protected page by LoginRequiredMiddleware),
  and only falls back to get_default_redirect_url() when there's no
  `next`. Overriding get_success_url() directly would have silently
  broken that "return to where you came from" behaviour for every role.

  Right now every role maps to the same shared dashboard, since
  per-role dashboards don't exist yet - only ONE mapping needs to
  change as real per-role dashboards get built in later phases; the
  login mechanics themselves never need to change again.
  """

  template_name = 'accounts/login.html'
  authentication_form = StyledAuthenticationForm
  redirect_authenticated_user = True

  ROLE_REDIRECTS = {
    User.Role.ADMIN: "dashboard:home",
    User.Role.TEACHER: "dashboard:home",
    User.Role.STUDENT: "dashboard:home",
    User.Role.PARENT: "dashboard:home",
    User.Role.STAFF: "dashboard:home",
  }

  def get_default_redirect_url(self):
    url_name = self.ROLE_REDIRECTS.get(self.request.user.role, "dashboard:home")
    return resolve_url(url_name)