"""Production settings."""
from config.settings.base import *  # noqa: F401, F403
import environ as _environ

_env = _environ.Env()

DEBUG = False   # ← was True — critical security fix

SECURE_HSTS_SECONDS           = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_SSL_REDIRECT           = _env.bool("SECURE_SSL_REDIRECT", default=False)
SESSION_COOKIE_SECURE         = True
CSRF_COOKIE_SECURE            = True
SECURE_CONTENT_TYPE_NOSNIFF   = True
X_FRAME_OPTIONS               = "DENY"

EMAIL_USE_SSL = _env.bool("EMAIL_USE_SSL", default=False)
EMAIL_USE_TLS = _env.bool("EMAIL_USE_TLS", default=True)

_sentry_dsn = _env("SENTRY_DSN", default="")
if _sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    sentry_sdk.init(
        dsn=_sentry_dsn,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )
