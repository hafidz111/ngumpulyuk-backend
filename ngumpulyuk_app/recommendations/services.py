from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from ngumpulyuk_app.events.models import Event
from ngumpulyuk_app.recommendations.models import RecommendationSignal


SIGNAL_WEIGHTS = {
    "view": Decimal("1.0"),
    "like": Decimal("2.0"),
    "join": Decimal("5.0"),
    "save": Decimal("3.0"),
    "share": Decimal("2.0"),
    "dislike": Decimal("-5.0"),
}


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


def record_recommendation_signal(
    *,
    user,
    event,
    signal_type: str,
    value: Decimal | int | float = Decimal("1"),
    dwell_ms: int | None = None,
    platform: str | None = None,
    source: str | None = None,
    dedupe_minutes: int | None = None,
):
    """
    Persist interaction signal. Optional dedupe for noisy repeated events (e.g. page views).
    """
    if user is None or not getattr(user, "is_authenticated", False):
        return None
    if event is None:
        return None
    if dedupe_minutes:
        since = timezone.now() - timedelta(minutes=dedupe_minutes)
        exists = RecommendationSignal.objects.filter(
            user=user,
            event=event,
            signal_type=signal_type,
            created_at__gte=since,
        ).exists()
        if exists:
            return None
    return RecommendationSignal.objects.create(
        user=user,
        event=event,
        signal_type=signal_type,
        value=Decimal(str(value)),
        dwell_ms=dwell_ms,
        platform=platform,
        source=source,
    )


def build_ml_profile(user):
    """
    Lightweight online-learning profile from user's historical signals.
    Learns per-category and per-time preferences with recency decay.
    """
    signals = (
        RecommendationSignal.objects.filter(user=user)
        .select_related("event")
        .order_by("-created_at")[:800]
    )
    now = timezone.now()
    category_scores: dict[str, Decimal] = {}
    time_scores: dict[str, Decimal] = {}
    location_scores: dict[str, Decimal] = {}
    total_abs = Decimal("0")

    for s in signals:
        ev = s.event
        if ev is None:
            continue
        days = max((now - s.created_at).days, 0)
        decay = Decimal("0.93") ** min(days, 45)
        base = SIGNAL_WEIGHTS.get(s.signal_type, Decimal("0")) * Decimal(s.value or 1)
        # views with short dwell are weak positive
        if s.signal_type == "view" and s.dwell_ms and s.dwell_ms < 3000:
            base = base * Decimal("0.3")
        weighted = base * decay
        total_abs += abs(weighted)

        if ev.category:
            category_scores[ev.category] = category_scores.get(ev.category, Decimal("0")) + weighted
        tb = _time_of_day_bucket(ev.event_time)
        if tb:
            time_scores[tb] = time_scores.get(tb, Decimal("0")) + weighted
        if ev.location_area:
            key = ev.location_area.strip().lower()
            location_scores[key] = location_scores.get(key, Decimal("0")) + weighted

    return {
        "category_scores": category_scores,
        "time_scores": time_scores,
        "location_scores": location_scores,
        "total_abs": total_abs,
    }


def ml_event_score(event: Event, profile: dict) -> tuple[Decimal, list[str]]:
    """
    Score event using learned profile. Returns score delta and human-readable reasons.
    """
    reasons: list[str] = []
    cat_map = profile.get("category_scores", {})
    time_map = profile.get("time_scores", {})
    loc_map = profile.get("location_scores", {})
    total_abs = profile.get("total_abs", Decimal("0"))
    if total_abs <= 0:
        return Decimal("0"), reasons

    score = Decimal("0")
    cat_score = cat_map.get(event.category or "", Decimal("0"))
    score += max(min(cat_score, Decimal("18")), Decimal("-18"))
    if cat_score > 0:
        reasons.append("Cocok dengan kategori yang sering kamu ikuti")
    elif cat_score < 0:
        reasons.append("Kurang cocok dengan pola aktivitasmu")

    tb = _time_of_day_bucket(event.event_time)
    if tb:
        tscore = time_map.get(tb, Decimal("0"))
        score += max(min(tscore, Decimal("8")), Decimal("-8"))
        if tscore > 0:
            reasons.append("Cocok dengan pola waktu aktivitasmu")

    if event.location_area:
        key = event.location_area.strip().lower()
        lscore = loc_map.get(key, Decimal("0"))
        score += max(min(lscore, Decimal("8")), Decimal("-8"))
        if lscore > 0:
            reasons.append("Cocok dengan lokasi yang sering kamu kunjungi")

    normalized = score / (Decimal("1") + (total_abs / Decimal("50")))
    normalized = max(min(normalized, Decimal("22")), Decimal("-22"))
    return normalized, reasons
