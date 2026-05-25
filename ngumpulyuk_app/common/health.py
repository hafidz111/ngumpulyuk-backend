"""Liveness/readiness probes — no auth, minimal work (for Render cold start & health checks)."""

from django.db import connection
from django.http import JsonResponse
from django.views import View


class HealthLivenessView(View):
    """Wake the dyno without touching the database."""

    def get(self, request):
        return JsonResponse({"status": "ok", "service": "ngumpulyuk-backend"})


class HealthReadinessView(View):
    """Optional DB check for deploy/orchestration (returns 503 if DB unavailable)."""

    def get(self, request):
        try:
            connection.ensure_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            response = JsonResponse(
                {"status": "not_ready", "database": "unavailable"},
                status=503,
            )
            response["Retry-After"] = "5"
            return response
        return JsonResponse({"status": "ready", "database": "ok"})
