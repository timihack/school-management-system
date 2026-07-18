"""
Base settings shared by every environment.
Environment-specific overrides live in dev.py / production.py.
"""
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "django_htmx",

    # Local apps
    "apps.accounts",
    "apps.dashboard",
    "apps.students",
    "apps.parents",
    "apps.departments",
    "apps.teachers",
    "apps.staff",

    # Third-party, security
    "axes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    # Enforces login-required on EVERY view by default. Views that must be
    # publicly reachable (login page, password reset, webhooks, etc.) opt
    # out explicitly via the login_not_required() decorator. This is a
    # deliberate secure-by-default choice: across ~25 modules, it's easier
    # to forget one @login_required than to forget one login_not_required
    # on a genuinely public view (which will fail loudly and immediately
    # in testing, rather than silently exposing a page).
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # AxesMiddleware MUST be the last middleware in this list - it needs
    # to see the final response after every other middleware (including
    # auth) has already run, to correctly attach lockout responses.
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

DATABASES = {
    "default": env.db("DATABASE_URL")
}

AUTH_USER_MODEL = "accounts.User"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "accounts:login"

# AxesBackend MUST be listed FIRST - it needs to intercept authentication
# attempts before Django's own ModelBackend, so it can block already-
# locked-out credentials before a real password check even happens.
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# Explicit rather than relying on library defaults, which have changed
# across major Axes versions (e.g. the default lockout status code
# changed from 403 to 429 in a past release) - pinning behavior here
# means an Axes upgrade can't silently change how lockouts work for us.
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # hour(s) before a lockout clears automatically
# Lock by the (username, IP) COMBINATION, not either alone: locking by
# username alone would let an attacker lock a real user out just by
# guessing their username repeatedly from anywhere; locking by IP alone
# would let a shared-IP attacker (school network, NAT) lock out every
# legitimate user behind that same IP.
AXES_LOCKOUT_PARAMETERS = ["username", "ip_address"]
AXES_RESET_ON_SUCCESS = True

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Redis / Celery
CELERY_BROKER_URL = env("REDIS_URL")
CELERY_RESULT_BACKEND = env("REDIS_URL")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"