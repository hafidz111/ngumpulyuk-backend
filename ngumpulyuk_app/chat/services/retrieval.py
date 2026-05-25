from __future__ import annotations

from datetime import timedelta
from typing import List

from django.db.models import Q
from django.utils import timezone

from ngumpulyuk_app.communities.models import Community, CommunityMember
from ngumpulyuk_app.events.models import Event
from ngumpulyuk_app.events.querysets import filter_scheduled_upcoming
from ngumpulyuk_app.events.serializers import event_list_item
from ngumpulyuk_app.recommendations.views import build_recommendations
from ngumpulyuk_app.users.models import UserPreferences


def _first_non_empty(*values):
    for v in values:
        if v:
            return v
    return None


def _user_preferred_location(user) -> str:
    try:
        return (user.preferences_row.preferred_location or "").strip()
    except UserPreferences.DoesNotExist:
        return ""


def _community_brief(c: Community, user):
    is_member = False
    if user and getattr(user, "is_authenticated", False):
        is_member = CommunityMember.objects.filter(community=c, user=user).exists()
    return {
        "id": str(c.id),
        "name": c.name,
        "description": (c.description or "")[:400],
        "category": c.category,
        "cover_image": c.cover_image,
        "logo": c.logo,
        "member_count": c.member_count,
        "is_verified": c.is_verified,
        "is_member": is_member,
    }


def fetch_event_cards(user, limit: int = 5):
    pairs = build_recommendations(user, min(limit, 10))
    cards = []
    for rec, ev in pairs[:limit]:
        payload = event_list_item(ev)
        cards.append(
            {
                "type": "event",
                "recommendation_reason": rec.reason,
                "image_url": _first_non_empty(payload.get("cover_image")),
                "payload": payload,
            }
        )
    return cards


def fetch_event_cards_by_query(
    user,
    message_lower: str,
    limit: int = 5,
    *,
    prefer_nearby: bool = False,
    prefer_weekend: bool = False,
):
    """
    Fallback retrieval when personalized recommendation has no candidate.
    """
    now_date = timezone.now().date()
    base_qs = filter_scheduled_upcoming(Event.objects.all(), today=now_date)
    qs = base_qs.exclude(creator=user)

    week_keys = ("minggu ini", "pekan ini", "week ini", "weekend", "week end", "sabtu", "minggu")
    if prefer_weekend or any(k in message_lower for k in week_keys):
        qs = qs.filter(event_date__lte=now_date + timedelta(days=7))

    pref_loc = _user_preferred_location(user)
    nearby_keys = ("deket", "dekat", "sekitar", "terdekat", "lokasiku", "lokasi ku", "dekat aku", "deket aku")
    if prefer_nearby or any(k in message_lower for k in nearby_keys):
        if pref_loc:
            qs = qs.filter(
                Q(location_area__icontains=pref_loc)
                | Q(location_address__icontains=pref_loc)
                | Q(title__icontains=pref_loc)
            )

    category_aliases = {
        "olahraga": ["olahraga", "sport", "sports", "futsal", "badminton", "basket", "lari", "jogging", "yoga", "gym"],
        "boardgame": ["board game", "boardgame", "board games", "tabletop", "kotak", "dnd"],
        "gaming": ["gaming", "game", "esport", "e-sport", "mobile legends", "mlbb"],
        "teknologi": ["teknologi", "tech", "coding", "programming", "developer", "ai"],
        "musik": ["musik", "music", "band", "konser", "gig"],
        "kreatif": [
            "kreatif",
            "creative",
            "seni",
            "art",
            "workshop",
            "lukis",
            "fotografi",
            "craft",
            "diy",
            "desain",
            "design",
            "tema",
            "temanya",
            "vibe",
        ],
    }

    q = Q()
    for aliases in category_aliases.values():
        if any(a in message_lower for a in aliases):
            for a in aliases:
                q |= Q(category__icontains=a) | Q(title__icontains=a) | Q(description__icontains=a)

    tokens = [t.strip() for t in message_lower.replace(",", " ").split() if len(t.strip()) >= 4]
    for t in tokens[:6]:
        q |= Q(title__icontains=t) | Q(description__icontains=t) | Q(category__icontains=t) | Q(location_area__icontains=t)

    if q:
        filtered = qs.filter(q).order_by("event_date", "event_time", "-created_at")
        if filtered.exists():
            qs = filtered
        else:
            qs = qs.order_by("event_date", "event_time", "-created_at")
    else:
        qs = qs.order_by("event_date", "event_time", "-created_at")

    rows = list(qs[:limit])
    # Last-resort fallback: if user only has self-created events, still show them.
    if not rows:
        qs_self = base_qs
        if any(k in message_lower for k in week_keys):
            qs_self = qs_self.filter(event_date__lte=now_date + timedelta(days=7))
        if q:
            filtered_self = qs_self.filter(q).order_by("event_date", "event_time", "-created_at")
            qs_self = filtered_self if filtered_self.exists() else qs_self.order_by("event_date", "event_time", "-created_at")
        else:
            qs_self = qs_self.order_by("event_date", "event_time", "-created_at")
        rows = list(qs_self[:limit])
    cards = []
    for ev in rows:
        payload = event_list_item(ev)
        cards.append(
            {
                "type": "event",
                "recommendation_reason": "Cocok dari kata kunci pertanyaan kamu",
                "image_url": _first_non_empty(payload.get("cover_image")),
                "payload": payload,
            }
        )
    return cards


def _dedupe_event_cards(cards: list) -> list:
    seen: set[str] = set()
    out: list = []
    for card in cards:
        eid = str(card.get("payload", {}).get("id", "")).strip()
        if not eid or eid in seen:
            continue
        seen.add(eid)
        out.append(card)
    return out


def fetch_event_cards_for_message(
    user,
    message_lower: str,
    limit: int = 5,
    *,
    prefer_nearby: bool = False,
    prefer_weekend: bool = False,
):
    """
    Prioritas: cocokkan kata kunci pertanyaan ke DB, lalu isi dengan rekomendasi personal.
    """
    merged: list = []
    merged.extend(
        fetch_event_cards_by_query(
            user,
            message_lower,
            limit,
            prefer_nearby=prefer_nearby,
            prefer_weekend=prefer_weekend,
        )
    )
    if len(merged) < limit:
        for card in fetch_event_cards(user, limit):
            merged.append(card)
            if len(merged) >= limit:
                break
    return _dedupe_event_cards(merged)[:limit]


def fetch_community_cards(user, message_lower: str, limit: int = 5):
    qs = Community.objects.select_related("creator").all()
    theme_aliases = [
        "kreatif",
        "creative",
        "seni",
        "art",
        "workshop",
        "lukis",
        "fotografi",
        "craft",
        "desain",
        "design",
        "tema",
        "temanya",
        "vibe",
    ]
    if any(a in message_lower for a in theme_aliases):
        q_theme = Q()
        for a in theme_aliases:
            q_theme |= Q(category__icontains=a) | Q(name__icontains=a) | Q(description__icontains=a)
        filtered_theme = qs.filter(q_theme).order_by("-member_count", "-created_at")
        if filtered_theme.exists():
            qs = filtered_theme

    active_keys = ("aktif", "rame", "ramai", "lagi rame", "yang lagi")
    if any(k in message_lower for k in active_keys):
        qs = qs.order_by("-member_count", "-created_at")
    else:
        # filter ringan dari teks (tanpa ML)
        tokens = [t for t in message_lower.replace(",", " ").split() if len(t) > 2]
        if tokens:
            q = Q()
            for t in tokens[:4]:
                q |= Q(name__icontains=t) | Q(description__icontains=t) | Q(category__icontains=t)
            filtered = qs.filter(q).order_by("-member_count", "-created_at")
            if filtered.exists():
                qs = filtered
    rows = list(qs.order_by("-member_count", "-created_at")[:limit])
    cards = []
    for c in rows:
        payload = _community_brief(c, user)
        cards.append(
            {
                "type": "community",
                "image_url": _first_non_empty(payload.get("cover_image"), payload.get("logo")),
                "payload": payload,
            }
        )
    return cards


def fetch_community_cards_for_message(user, message_lower: str, limit: int = 5):
    """
    Prioritas: filter dari kata kunci pertanyaan, fallback komunitas populer di platform.
    """
    cards = fetch_community_cards(user, message_lower, limit)
    if cards:
        return cards
    rows = list(
        Community.objects.select_related("creator").order_by("-member_count", "-created_at")[:limit]
    )
    out = []
    for c in rows:
        payload = _community_brief(c, user)
        out.append(
            {
                "type": "community",
                "image_url": _first_non_empty(payload.get("cover_image"), payload.get("logo")),
                "payload": payload,
            }
        )
    return out


def fetch_area_cards(user, limit: int = 8, *, prefer_nearby: bool = False):
    """
    'Tempat' = area/kota dari event upcoming (bukan POI pihak ketiga) — jujur, tanpa halusinasi nama venue baru.
    """
    areas = (
        filter_scheduled_upcoming(Event.objects.all())
        .exclude(location_area="")
        .values_list("location_area", flat=True)
        .distinct()[:80]
    )
    uniq = []
    seen = set()
    pref = _user_preferred_location(user).lower()
    if prefer_nearby and pref:
        uniq = [a for a in uniq if pref in a.lower()] or uniq
    for a in areas:
        key = (a or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        uniq.append(a.strip())
    if pref:
        uniq.sort(key=lambda x: (0 if pref in x.lower() else 1, -len(x)))
    else:
        uniq.sort(key=lambda x: -len(x))
    out = [{"type": "area", "payload": {"name": name, "hint": "Area dari event aktif di platform."}} for name in uniq[:limit]]
    return out


def context_bundle_for_llm(
    *,
    intent: str,
    faq_snippets: List[dict],
    event_summaries: List[str],
    community_summaries: List[str],
    areas: List[str],
):
    lines = [f"Intent: {intent}", "Konteks resmi (pakai ini saja, jangan mengarang fakta baru):"]
    if faq_snippets:
        lines.append("FAQ:")
        for f in faq_snippets:
            lines.append(f"- {f['title']}: {f['answer'][:500]}")
    if event_summaries:
        lines.append("Event (id | judul | kategori | area):")
        for s in event_summaries:
            lines.append(f"- {s}")
    if community_summaries:
        lines.append("Komunitas (id | nama | kategori):")
        for s in community_summaries:
            lines.append(f"- {s}")
    if areas:
        lines.append("Area yang sering dipakai event:")
        lines.append(", ".join(areas[:12]))
    return "\n".join(lines)
