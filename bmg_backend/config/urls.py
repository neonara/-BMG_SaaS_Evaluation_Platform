"""
config/urls.py — Root URL configuration.
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView
from config.urls_docs import docs_urlpatterns
from apps.users.views import CustomTokenObtainPairView
from core.health.views import HealthCheckView

urlpatterns = [
    # ── Health check (no auth, no tenant required) ───────────
    path("api/health/", HealthCheckView.as_view(), name="health_check"),

    # ── JWT Auth ──────────────────────────────────────────────
    path("api/auth/token/",         CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(),          name="token_refresh"),
    path("api/auth/",               include("apps.users.urls.auth")),

    # ── API v1 ────────────────────────────────────────────────
    path("api/v1/", include("config.api_router")),

    # ── Admin ─────────────────────────────────────────────────
    path("bmg-admin/", admin.site.urls),
]
urlpatterns += docs_urlpatterns                  


if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
    except ImportError:
        pass
