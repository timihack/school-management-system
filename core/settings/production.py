from .base import *  # noqa

DEBUG = False

MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

# NOTE: STATICFILES_STORAGE / DEFAULT_FILE_STORAGE were removed in Django 5.1.
# The STORAGES dict (introduced in 4.2) is now the only valid way to configure
# storage backends. Setting the old-style STATICFILES_STORAGE alongside STORAGES
# raises ImproperlyConfigured ("mutually exclusive").
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
X_FRAME_OPTIONS = "DENY"