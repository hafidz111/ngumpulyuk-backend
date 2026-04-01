from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from ngumpulyuk_app.common.api_response import ok
from ngumpulyuk_app.common.presenters import clamp_limit
from ngumpulyuk_app.events.models import Event
from ngumpulyuk_app.events.serializers import event_list_item
from ngumpulyuk_app.recommendations.models import AiRecommendation
from ngumpulyuk_app.users.models import UserInterest, UserPreferences

RECOMMENDATIONS_TAG = ["Recommendations"]


def build_recommendations(user, limit=10):
    AiRecommendation.objects.filter(user=user, expires_at__lt=timezone.now()).delete()
    interests = set(UserInterest.objects.filter(user=user).values_list("interest_name", flat=True))
    try:
        pref = user.preferences_row
        pref_time = pref.preferred_time
        pref_loc = pref.preferred_location
    except UserPreferences.DoesNotExist:
        pref_time = None
        pref_loc = None
    qs = Event.objects.filter(status="upcoming").exclude(creator=user)
    if interests:
        narrowed = qs.filter(category__in=interests)
        if narrowed.exists():
            qs = narrowed
    qs = qs.order_by("-created_at")[:50]
    out = []
    for ev in qs:
        score = Decimal("50.0")
        reason_parts = []
        if ev.category in interests:
            score += Decimal("25")
            reason_parts.append(f"Matches your interest in {ev.category}")
        if pref_time and pref_time == "evening":
            score += Decimal("10")
            reason_parts.append("Preferred time evening")
        if pref_loc and pref_loc.lower() in (ev.location_area or "").lower():
            score += Decimal("15")
            reason_parts.append("Preferred location")
        score = min(score, Decimal("100"))
        reason = "; ".join(reason_parts) if reason_parts else "Popular upcoming event"
        rec, _ = AiRecommendation.objects.update_or_create(
            user=user,
            event=ev,
            defaults={
                "score": score,
                "reason": reason,
                "expires_at": timezone.now() + timedelta(days=7),
            },
        )
        out.append((rec, ev))
        if len(out) >= limit:
            break
    return out


@extend_schema_view(
    get=extend_schema(tags=RECOMMENDATIONS_TAG, summary="Rekomendasi event"),
)
class RecommendationsEventsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        limit = clamp_limit(request.query_params.get("limit"), 10, max_val=100)
        pairs = build_recommendations(request.user, limit)
        data = []
        for rec, ev in pairs:
            data.append(
                {
                    "event": event_list_item(ev),
                    "score": float(rec.score),
                    "reason": rec.reason,
                }
            )
        return ok({"recommendations": data})


@extend_schema_view(
    post=extend_schema(tags=RECOMMENDATIONS_TAG, summary="Segarkan rekomendasi"),
)
class RecommendationsRefreshView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        AiRecommendation.objects.filter(user=request.user).delete()
        pairs = build_recommendations(request.user, 10)
        return ok({"count": len(pairs)}, message="Recommendations refreshed")
