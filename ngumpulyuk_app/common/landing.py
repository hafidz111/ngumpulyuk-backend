from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from ngumpulyuk_app.common.api_response import ok
from ngumpulyuk_app.common.openapi_responses import R200
from ngumpulyuk_app.communities.models import Community
from ngumpulyuk_app.communities.views import community_dict, community_queryset_with_stats
from ngumpulyuk_app.events.models import Event, EventParticipant
from ngumpulyuk_app.events.querysets import filter_scheduled_past, filter_scheduled_upcoming
from ngumpulyuk_app.events.serializers import event_list_item

PUBLIC_TAG = ["Public"]


def _format_spotlight_event(ev):
    if not ev:
        return None
    return {
        "id": str(ev.id),
        "title": ev.title,
        "category": ev.category or "",
        "location_area": ev.location_area or "",
    }


def _member_preview_item(user):
    return {
        "id": str(user.id),
        "full_name": user.full_name or "",
        "username": user.username or "",
        "profile_picture": user.profile_picture or None,
    }


def _collect_social_members(User):
    preview = []
    seen_ids = set()

    participant_rows = (
        EventParticipant.objects.filter(status="confirmed")
        .select_related("user")
        .order_by("-joined_at")[:24]
    )
    for row in participant_rows:
        uid = row.user_id
        if uid in seen_ids:
            continue
        seen_ids.add(uid)
        preview.append(_member_preview_item(row.user))
        if len(preview) >= 8:
            break

    if len(preview) < 8:
        for user in User.objects.filter(is_active=True).order_by("-created_at")[:24]:
            if user.id in seen_ids:
                continue
            seen_ids.add(user.id)
            preview.append(_member_preview_item(user))
            if len(preview) >= 8:
                break

    total = User.objects.filter(is_active=True).count()
    return {"total": total, "preview": preview}


def _featured_events_for_landing(*, limit=8):
    """
    Kartu landing: utamakan event akan datang (paling banyak peserta),
    lalu isi dari event yang sudah lewat jika belum penuh.
    """
    base = Event.objects.select_related("creator").exclude(status="cancelled")
    upcoming_qs = filter_scheduled_upcoming(base)
    featured = list(
        upcoming_qs.order_by("-current_participants", "event_date", "event_time")[:limit]
    )
    if len(featured) >= limit:
        return featured

    used_ids = {e.id for e in featured}
    remaining = limit - len(featured)
    past = list(
        filter_scheduled_past(base)
        .exclude(id__in=used_ids)
        .order_by("-current_participants", "-event_date", "-event_time")[:remaining]
    )
    featured.extend(past)
    return featured


@extend_schema(
    tags=PUBLIC_TAG,
    summary="Konten landing page (publik)",
    responses=R200,
)
class LandingPublicView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        User = get_user_model()
        now = timezone.now()
        week_ago = now - timedelta(days=7)

        users_count = User.objects.filter(is_active=True).count()
        communities_count = Community.objects.count()
        upcoming_qs = filter_scheduled_upcoming(Event.objects.select_related("creator"))
        upcoming_count = upcoming_qs.count()
        events_total = Event.objects.exclude(status="cancelled").count()
        participants_total = EventParticipant.objects.filter(status="confirmed").count()
        recent_joins = EventParticipant.objects.filter(
            status="confirmed",
            joined_at__gte=week_ago,
        ).count()

        featured_events_models = _featured_events_for_landing(limit=8)
        featured_events = [event_list_item(e, is_joined=False) for e in featured_events_models]
        spotlight_model = upcoming_qs.order_by(
            "-current_participants", "event_date", "event_time"
        ).first()

        communities_qs = (
            community_queryset_with_stats()
            .order_by("-member_count", "-created_at")[:6]
        )
        featured_communities = [
            community_dict(c, request.user if request.user.is_authenticated else None)
            for c in communities_qs
        ]

        spotlight = spotlight_model
        hero_image = None
        if spotlight and spotlight.cover_image:
            hero_image = spotlight.cover_image
        elif featured_communities:
            hero_image = featured_communities[0].get("cover_image") or featured_communities[0].get("logo")

        social_members = _collect_social_members(User)

        final_image = hero_image
        if not final_image and len(featured_events_models) > 1:
            second = featured_events_models[1]
            if second and second.cover_image:
                final_image = second.cover_image

        return ok(
            {
                "stats": {
                    "users": users_count,
                    "communities": communities_count,
                    "events": events_total,
                    "events_upcoming": upcoming_count,
                    "events_total": events_total,
                    "participants": participants_total,
                    "recent_joins_week": recent_joins,
                },
                "featured_events": featured_events,
                "featured_communities": featured_communities,
                "hero": {
                    "image": hero_image,
                    "final_image": final_image,
                    "spotlight_event": _format_spotlight_event(spotlight),
                    "social_members": social_members,
                },
            }
        )
