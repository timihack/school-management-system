from .dev import *  # noqa

# django-axes' own changelog explicitly documents this: "Add AXES_ENABLED
# setting for disabling Axes with e.g. tests that use Django test client
# login, logout, and force_login methods, which do not supply the
# request argument to views, preventing Axes from functioning correctly
# in certain test setups." Nearly every test in this suite uses
# force_login() for speed - leaving Axes enabled here would make those
# tests fail or behave unpredictably for reasons unrelated to what
# they're actually testing.
#
# The one test that DOES need Axes active (proving lockout actually
# works) re-enables it locally via the `settings` fixture - see
# apps/accounts/tests/test_lockout.py.
AXES_ENABLED = False