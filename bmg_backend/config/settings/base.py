"""
Base settings — shared by all environments.
Never import this directly; use development.py, production.py, or test.py.
"""
from pathlib import Path

import environ

# ── Paths ─────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ── Environment ───────────────────────────────────────────────────
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# ── django-tenants ────────────────────────────────────────────────
# CRITICAL: DATABASE_ROUTERS must be set before any DB access.
# The public schema holds: TENANT, DOMAIN, PACK, PAYMENT, INVOICE,
#                          AUDIT_LOG, VOUCHER, PACK_USER_ACCESS
# Each tenant schema holds: USER, TEST_MODEL, SESSION, TEST_ATTEMPT, etc.

DATABASE_ROUTERS = ["django_tenants.routers.TenantSyncRouter"]

SHARED_APPS = [
    # django-tenants MUST be first
    "django_tenants",
    # Django built-ins (shared schema)
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party (shared)
    "rest_framework",
    "corsheaders",
    "django_celery_beat",
    "django_celery_results",
    "graphene_django",
    # BMG shared apps
    "apps.tenants",      # TENANT, DOMAIN models
    #"apps.packs",        # PACK, PACK_TEST, VOUCHER, PACK_USER_ACCESS
    #"apps.payments",     # PAYMENT, INVOICE
    "apps.audit",        # AUDIT_LOG
]

TENANT_APPS = [
    # Django built-ins (per-tenant schema)
    "django.contrib.auth",
    "django.contrib.contenttypes",
    # BMG tenant-scoped apps
    "apps.users",            # USER (tenant-scoped)
    #"apps.tests_module",     # TEST_MODEL, QUESTION, ANSWER_OPTION,
                             # RESULT_BAND, PROFILE_DEFINITION
   # "apps.sessions_module",  # SESSION, SESSION_ASSIGNMENT
   # "apps.attempts",         # TEST_ATTEMPT, CANDIDATE_ANSWER
   # "apps.results",          # SHAREABLE_REPORT
   # "apps.notifications",    # NOTIFICATION
]

INSTALLED_APPS = list(SHARED_APPS) + [
    app for app in TENANT_APPS if app not in SHARED_APPS
]

# django-tenants: which model stores tenants
TENANT_MODEL = "tenants.Tenant"
TENANT_DOMAIN_MODEL = "tenants.Domain"

# ── Middleware ────────────────────────────────────────────────────
MIDDLEWARE = [
    # 1. Tenant resolution (MUST be first)
    "django_tenants.middleware.main.TenantMainMiddleware",
    # 2. Security
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # 3. CORS
    "corsheaders.middleware.CorsMiddleware",
    # 4. Standard Django
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # 5. Custom BMG middleware
    "core.middleware.jwt_middleware.JWTAuthMiddleware",
    "core.middleware.rbac_middleware.RBACMiddleware",
    "core.middleware.audit_middleware.AuditMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"

# ── Database ──────────────────────────────────────────────────────
DATABASES = {
    "default": env.db("DATABASE_URL"),
}
DATABASES["default"]["ENGINE"] = "django_tenants.postgresql_backend"

# ── Cache (Redis) ─────────────────────────────────────────────────
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "bmg",
        "TIMEOUT": 300,
    }
}

# ── Auth ──────────────────────────────────────────────────────────
AUTH_USER_MODEL = "users.User"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── REST Framework ────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
}

# ── JWT ───────────────────────────────────────────────────────────
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    # Custom claims — add tenant_schema + role to payload
    "TOKEN_OBTAIN_SERIALIZER": "apps.users.serializers.CustomTokenObtainPairSerializer",
}

# ── GraphQL ───────────────────────────────────────────────────────
GRAPHENE = {
    "SCHEMA": "config.schema.schema",
    "MIDDLEWARE": [
        "graphql_jwt.middleware.JSONWebTokenMiddleware",
    ],
}

# ── Celery ────────────────────────────────────────────────────────
CELERY_BROKER_URL = env("RABBITMQ_URL")
CELERY_RESULT_BACKEND = env("REDIS_URL")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Africa/Tunis"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TASK_ROUTES = {
    "apps.attempts.tasks.*": {"queue": "scoring"},
    "apps.results.tasks.*":  {"queue": "pdf"},
    "apps.notifications.tasks.*": {"queue": "notif"},
    "apps.users.tasks.*":    {"queue": "email"},
    "*":                     {"queue": "default"},
}

# ── Email ─────────────────────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("SMTP_HOST", default="localhost")
EMAIL_PORT = env.int("SMTP_PORT", default=587)
EMAIL_HOST_USER = env("SMTP_USER", default="")
EMAIL_HOST_PASSWORD = env("SMTP_PASSWORD", default="")
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="BMG <no-reply@bmg.tn>")

# ── Storage (Cloudinary) ──────────────────────────────────────────
DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
CLOUDINARY_STORAGE = {"CLOUDINARY_URL": env("CLOUDINARY_URL", default="")}

# ── Static files ──────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ── Internationalisation ──────────────────────────────────────────
LANGUAGE_CODE = "en-us"
LANGUAGES = [("en", "English"), ("fr", "French"), ("ar", "Arabic")]
TIME_ZONE = "Africa/Tunis"
USE_I18N = True
USE_TZ = True

# ── External service URLs ─────────────────────────────────────────
GOTENBERG_URL = env("GOTENBERG_URL", default="http://gotenberg:3001")
SELENIUM_URL  = env("SELENIUM_URL",  default="http://selenium_grid:4444/wd/hub")
FRONTEND_URL  = env("FRONTEND_URL",  default="https://app.bmg.tn")
VITRINE_URL   = env("VITRINE_URL",   default="https://bmg.tn")

# ── CORS ──────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [
    env("FRONTEND_URL", default="https://app.bmg.tn"),
    env("VITRINE_URL",  default="https://bmg.tn"),
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── API Documentation (drf-spectacular) ───────────────────────────────────────
from config.api_docs import SPECTACULAR_SETTINGS  # noqa: F401, E402

# ── Throttle settings ─────────────────────────────────────────────────────────
from config.settings.throttle_settings import (  # noqa: F401, E402
    DEFAULT_THROTTLE_RATES,
    REST_FRAMEWORK_THROTTLE_CLASSES,
)

REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = REST_FRAMEWORK_THROTTLE_CLASSES  # noqa: F821
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = DEFAULT_THROTTLE_RATES  # noqa: F821

# ── Celery Beat schedule ──────────────────────────────────────────────────────
from config.celery_beat_schedule import CELERY_BEAT_SCHEDULE  # noqa: F401, E402
