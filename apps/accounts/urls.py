from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    # login_not_required is required here: LoginRequiredMiddleware protects
    # every view by default, and the login page itself must obviously be
    # reachable by users who are NOT yet logged in.
    path(
        "login/",
        login_not_required(views.RoleBasedLoginView.as_view()),
        name="login",
    ),
    # LogoutView needs no such exemption - a user hitting /logout/ is, by
    # definition, already authenticated when they land here.
    path("logout/", LogoutView.as_view(), name="logout"),
]