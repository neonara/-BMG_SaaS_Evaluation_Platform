"""
Base settings — shared by all environments.
"""
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    environ.Env.read_env(_env_file)

SECRET_KEY    = env("SECRET_KEY")
DEBUG         = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# ── django-tenants ────────────────────────────────────────────
DATABASE_ROUTERS = ["django_tenants.routers.TenantSyncRouter"]

# KEY FIX: When no tenant domain matches the request host,
# serve the PUBLIC schema instead of returning 404.
# Required for: health checks, admin, public API endpoints.
SHOW_PUBLIC_IF_NO_TENANT_FOUND = True

SHARED_APPS = [
    "django_tenants",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "django.contrib.messages",
    "rest_framework",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "corsheaders",
    "django_filters",
    "django_celery_beat",
    "django_celery_results",
    "graphene_django",
    # BMG shared apps
    "apps.tenants",
    "apps.audit",
    "apps.multi_language",
]

# users lives in TENANT schema only — NOT in SHARED_APPS
TENANT_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "apps.users",
    "apps.social_accounts",
]

INSTALLED_APPS = list(SHARED_APPS) + [
    app for app in TENANT_APPS if app not in SHARED_APPS
]

TENANT_MODEL        = "tenants.Tenant"
TENANT_DOMAIN_MODEL = "tenants.Domain"

# ── Middleware ────────────────────────────────────────────────
MIDDLEWARE = [
    "django_tenants.middleware.main.TenantMainMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.jwt_middleware.JWTAuthMiddleware",
    "core.middleware.rbac_middleware.RBACMiddleware",
    "core.middleware.audit_middleware.AuditMiddleware",
]

ROOT_URLCONF     = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

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

# ── Database ──────────────────────────────────────────────────
DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["ENGINE"] = "django_tenants.postgresql_backend"

# ── Cache ─────────────────────────────────────────────────────
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://redis:6379/0"),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        "KEY_PREFIX": "bmg",
        "TIMEOUT": 300,
    }
}

# ── Auth ──────────────────────────────────────────────────────
AUTH_USER_MODEL = "users.User"
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
# ── API Docs ──────────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    "TITLE": "BMG Platform API",
    "VERSION": "1.0.0",
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
}
# ── REST Framework ────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
}

# ── JWT ───────────────────────────────────────────────────────
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":  timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS":  True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "TOKEN_OBTAIN_SERIALIZER": "apps.users.serializers.CustomTokenObtainPairSerializer",
}

# ── GraphQL ───────────────────────────────────────────────────
GRAPHENE = {"SCHEMA": "config.schema.schema", "MIDDLEWARE": []}
# ── Celery ────────────────────────────────────────────────────
CELERY_BROKER_URL        = env("RABBITMQ_URL", default="amqp://guest:guest@rabbitmq:5672/")
CELERY_RESULT_BACKEND    = env("REDIS_URL",    default="redis://redis:6379/0")
CELERY_ACCEPT_CONTENT    = ["json"]
CELERY_TASK_SERIALIZER   = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE          = "Africa/Tunis"
CELERY_BEAT_SCHEDULER    = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TASK_ROUTES = {
    "apps.attempts.tasks.*":      {"queue": "scoring"},
    "apps.results.tasks.*":       {"queue": "pdf"},
    "apps.notifications.tasks.*": {"queue": "notif"},
    "apps.users.tasks.*":         {"queue": "email"},
    "*":                          {"queue": "default"},
}

# ── Email ─────────────────────────────────────────────────────
EMAIL_BACKEND       = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST          = env("SMTP_HOST",     default="localhost")
EMAIL_PORT          = env.int("SMTP_PORT", default=587)
EMAIL_HOST_USER     = env("SMTP_USER",     default="")
EMAIL_HOST_PASSWORD = env("SMTP_PASSWORD", default="")
EMAIL_USE_TLS       = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL       = env.bool("EMAIL_USE_SSL", default=False)
DEFAULT_FROM_EMAIL  = env("DEFAULT_FROM_EMAIL", default="BMG <no-reply@bmg.tn>")

# ── Storage ───────────────────────────────────────────────────
_cloudinary_url = env("CLOUDINARY_URL", default="")
if _cloudinary_url:
    DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
    CLOUDINARY_STORAGE   = {"CLOUDINARY_URL": _cloudinary_url}
else:
    DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

# ── Static files ──────────────────────────────────────────────
STATIC_URL  = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ── i18n ─────────────────────────────────────────────────────
from django.utils.translation import gettext_lazy as _

LANGUAGE_CODE = "en"
TIME_ZONE     = "Africa/Tunis"
USE_I18N      = True
USE_L10N      = True
USE_TZ        = True

LANGUAGES = [
    ("en", _("English")),
    ("fr", _("French")),
    ("ar", _("Arabic")),
]
LOCALE_PATHS = [BASE_DIR / "locale"]

# Arabic is RTL — the frontend reads this via /api/v1/languages/
LANGUAGE_RTL_CODES = ["ar"]

# ── External services ─────────────────────────────────────────
GOTENBERG_URL = env("GOTENBERG_URL", default="http://gotenberg:3001")
SELENIUM_URL  = env("SELENIUM_URL",  default="http://selenium_grid:4444/wd/hub")
FRONTEND_URL  = env("FRONTEND_URL",  default="http://localhost:3000")
VITRINE_URL   = env("VITRINE_URL",   default="http://localhost:3001")

# ── CORS ──────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [
    env("FRONTEND_URL", default="http://localhost:3000"),
    env("VITRINE_URL",  default="http://localhost:3001"),
]
CORS_ALLOW_CREDENTIALS = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Throttle settings ─────────────────────────────────────────
from config.settings.throttle_settings import (  # noqa: E402
    DEFAULT_THROTTLE_RATES,
    REST_FRAMEWORK_THROTTLE_CLASSES,
)
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = REST_FRAMEWORK_THROTTLE_CLASSES
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]   = DEFAULT_THROTTLE_RATES


# ── Social OAuth ──────────────────────────────────────────────
SOCIAL_AUTH_GOOGLE_CLIENT_ID       = env("GOOGLE_CLIENT_ID",       default="")
SOCIAL_AUTH_GOOGLE_CLIENT_SECRET   = env("GOOGLE_CLIENT_SECRET",   default="")
SOCIAL_AUTH_GOOGLE_REDIRECT_URI    = env("GOOGLE_REDIRECT_URI",    default="http://localhost:8000/api/v1/auth/social/google/callback/")

SOCIAL_AUTH_LINKEDIN_CLIENT_ID     = env("LINKEDIN_CLIENT_ID",     default="")
SOCIAL_AUTH_LINKEDIN_CLIENT_SECRET = env("LINKEDIN_CLIENT_SECRET", default="")
SOCIAL_AUTH_LINKEDIN_REDIRECT_URI  = env("LINKEDIN_REDIRECT_URI",  default="http://localhost:8000/api/v1/auth/social/linkedin/callback/")

# ── Celery Beat schedule ──────────────────────────────────────
from config.celery_beat_schedule import CELERY_BEAT_SCHEDULE  # noqa: E402
