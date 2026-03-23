"""
Central DRF router — registers all app ViewSets under /api/v1/.
Each app plugs in its own router via include().
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

urlpatterns = [
    # ── Tenants / Organisations ──────────────────────────────────
    path("tenants/",      include("apps.tenants.urls")),

    # ── Users & Auth ─────────────────────────────────────────────
    path("users/",        include("apps.users.urls.users")),

    # ── Test models ──────────────────────────────────────────────
    # path("tests/",        include("apps.tests_module.urls")),

    # # ── Packs & Vouchers ─────────────────────────────────────────
    # path("packs/",        include("apps.packs.urls")),
    # path("public/packs/", include("apps.packs.urls_public")),  # Vitrine API (no auth)

    # # ── Sessions ─────────────────────────────────────────────────
    # path("sessions/",     include("apps.sessions_module.urls")),

    # # ── Test attempts ────────────────────────────────────────────
    # path("attempts/",     include("apps.attempts.urls")),

    # # ── Results & Reports ────────────────────────────────────────
    # path("results/",      include("apps.results.urls")),
    # path("reports/",      include("apps.results.urls_public")),  # Shareable reports (no auth)

    # # ── Payments ─────────────────────────────────────────────────
    # path("payments/",     include("apps.payments.urls")),
    # path("webhooks/",     include("apps.payments.urls_webhooks")),  # Payment gateway webhooks

    # # ── Notifications ────────────────────────────────────────────
    # path("notifications/", include("apps.notifications.urls")),

    # # ── Audit log (Super Admin only) ─────────────────────────────
    # path("audit/",        include("apps.audit.urls")),

    # ── DRF router ───────────────────────────────────────────────
    path("", include(router.urls)),
]
