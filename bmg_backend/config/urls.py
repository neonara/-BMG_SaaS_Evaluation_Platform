"""
Root URL configuration.
django-tenants routes requests by subdomain — this file handles
the shared (public) URL space plus API and GraphQL endpoints.
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from graphene_django.views import GraphQLView
from rest_framework_simplejwt.views import TokenRefreshView

from apps.users.views import CustomTokenObtainPairView

urlpatterns = [
    # ── Health check (used by Docker + CI) ──────────────────────
    path("api/health/", include("core.health.urls")),

    # ── Auth endpoints ───────────────────────────────────────────
    path("api/auth/token/",         CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(),          name="token_refresh"),
    path("api/auth/",               include("apps.users.urls.auth")),

    # ── API v1 ───────────────────────────────────────────────────
    path("api/v1/", include("config.api_router")),

    # ── GraphQL ──────────────────────────────────────────────────
    path("graphql/", GraphQLView.as_view(graphiql=settings.DEBUG)),

    # ── Admin (Super Admin BMG only) ─────────────────────────────
  #  path("bmg-admin/", admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
