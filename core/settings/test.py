from .dev import *  # noqa

import tempfile

# Isolates file uploads created during tests (e.g. Student.photo in
# test_photo_upload.py) to a throwaway temp directory instead of the
# real project media/ folder. Without this, every test run would leave
# actual uploaded test images behind in MEDIA_ROOT, accumulating
# indefinitely across test runs - a classic case of tests having a real
# side effect on the filesystem that has nothing to do with what they're
# actually verifying.
MEDIA_ROOT = tempfile.mkdtemp()

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