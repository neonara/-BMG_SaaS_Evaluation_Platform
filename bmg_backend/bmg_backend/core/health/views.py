"""core/health/views.py"""
from django.db import connection
from django.core.cache import cache
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    permission_classes     = [AllowAny]
    authentication_classes = []

    def get(self, request):
        checks = {}

        try:
            with connection.cursor() as c:
                c.execute("SELECT 1")
            checks["db"] = "ok"
        except Exception as e:
            checks["db"] = "error: %s" % str(e)[:80]

        try:
            cache.set("_health_check", "ok", 5)
            checks["cache"] = "ok" if cache.get("_health_check") == "ok" else "miss"
        except Exception as e:
            checks["cache"] = "error: %s" % str(e)[:80]

        ok = all(v == "ok" for v in checks.values())
        return Response(
            {"status": "ok" if ok else "degraded", **checks},
            status=200 if ok else 503,
        )
