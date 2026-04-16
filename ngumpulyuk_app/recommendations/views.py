from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from ngumpulyuk_app.common.api_response import err, ok
from ngumpulyuk_app.common.openapi_params import q_int
from ngumpulyuk_app.common.openapi_responses import R200
from ngumpulyuk_app.common.presenters import clamp_limit
from ngumpulyuk_app.events.models import Event
from ngumpulyuk_app.events.serializers import event_list_item
from ngumpulyuk_app.recommendations.models import AiRecommendation, RecommendationSignal
from ngumpulyuk_app.recommendations.serializers import RecommendationSignalWriteSerializer
from ngumpulyuk_app.recommendations.services import (
    SIGNAL_WEIGHTS,
    build_ml_profile,
    ml_event_score,
    record_recommendation_signal,
)
from ngumpulyuk_app.users.models import UserInterest, UserPreferences

RECOMMENDATIONS_TAG = ["Recommendations"]


def _time_of_day_bucket(dt_time):
    if dt_time is None:
        return None
    h = dt_time.hour
    if 5 <= h < 11:
        return "morning"
    if 11 <= h < 16:
        return "afternoon"
    if 16 <= h < 20:
        return "evening"
    return "night"


def _behavior_score(user, ev):
    now = timezone.now()
    signals = RecommendationSignal.objects.filter(user=user, event=ev).order_by("-created_at")[:50]
    if not signals:
        return Decimal("0"), []

    total = Decimal("0")
    reasons = []
    for s in signals:
        days = max((now - s.created_at).days, 0)
        decay = Decimal("0.92") ** min(days, 30)
        weight = SIGNAL_WEIGHTS.get(s.signal_type, Decimal("0")) * Decimal(s.value or 1)
        if s.signal_type == "view" and s.dwell_ms and s.dwell_ms >= 15000:
            weight += Decimal("0.5")
        score = weight * decay
        total += score
    if total > 0:
        reasons.append("Based on your interactions")
    elif total < 0:
        reasons.append("Reduced due to negative interactions")
    return total, reasons


def _user_preference_bonus(user, ev, interests, pref_time, pref_loc):
    score = Decimal("0")
    reasons = []
    if ev.category in interests:
        score += Decimal("18")
        reasons.append(f"Matches your interest in {ev.category}")
    if pref_time and _time_of_day_bucket(ev.event_time) == pref_time:
        score += Decimal("8")
        reasons.append(f"Matches your preferred time ({pref_time})")
    if pref_loc and pref_loc.lower() in (ev.location_area or "").lower():
        score += Decimal("10")
        reasons.append("Near your preferred location")
    return score, reasons


def _popularity_bonus(ev):
    joiners = Decimal(ev.current_participants or 0)
    return min(joiners * Decimal("0.6"), Decimal("12"))


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
    disliked_ids = set(
        RecommendationSignal.objects.filter(user=user, signal_type="dislike")
        .values_list("event_id", flat=True)
    )
    qs = (
        Event.objects.filter(status="upcoming")
        .exclude(creator=user)
        .exclude(id__in=disliked_ids)
        .annotate(trending=Count("participants", filter=Q(participants__status="confirmed")))
        .order_by("-trending", "-created_at")[:120]
    )
    ml_profile = build_ml_profile(user)
    out = []
    for ev in qs:
        score = Decimal("35.0")
        reason_parts = []
        pref_score, pref_reason = _user_preference_bonus(user, ev, interests, pref_time, pref_loc)
        behavior_score, behavior_reason = _behavior_score(user, ev)
        ml_score, ml_reasons = ml_event_score(ev, ml_profile)
        popularity = _popularity_bonus(ev)
        # recency bonus for fresh upcoming events
        recency = Decimal("8") if (timezone.now().date() - ev.created_at.date()).days <= 2 else Decimal("0")
        score += pref_score + behavior_score + ml_score + popularity + recency
        reason_parts.extend(pref_reason)
        reason_parts.extend(behavior_reason)
        reason_parts.extend(ml_reasons)
        if popularity > 0:
            reason_parts.append("Popular event")
        if recency > 0:
            reason_parts.append("Recently added")
        score = max(Decimal("0"), min(score, Decimal("100")))
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
    get=extend_schema(
        tags=RECOMMENDATIONS_TAG,
        summary="Rekomendasi event",
        parameters=[q_int("limit", "Jumlah rekomendasi (default 10, max 100)", 10)],
        responses=R200,
    ),
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
    post=extend_schema(
        tags=RECOMMENDATIONS_TAG,
        summary="Segarkan rekomendasi",
        request=None,
        responses=R200,
    ),
)
class RecommendationsRefreshView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        AiRecommendation.objects.filter(user=request.user).delete()
        pairs = build_recommendations(request.user, 10)
        return ok({"count": len(pairs)}, message="Recommendations refreshed")


@extend_schema_view(
    post=extend_schema(
        tags=RECOMMENDATIONS_TAG,
        summary="Catat signal interaksi recommendation",
        request=RecommendationSignalWriteSerializer,
        responses=R200,
    ),
)
class RecommendationSignalView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = RecommendationSignalWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        v = ser.validated_data
        ev = Event.objects.filter(pk=v["event_id"]).first()
        if not ev:
            return err("NOT_FOUND", "Event not found", 404)
        record_recommendation_signal(
            user=request.user,
            event=ev,
            signal_type=v["signal_type"],
            value=v.get("value", Decimal("1")),
            dwell_ms=v.get("dwell_ms"),
            platform=v.get("platform"),
            source=(v.get("source") or "").strip() or None,
        )
        return ok(message="Signal recorded")
