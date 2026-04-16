from datetime import datetime

from django.contrib.auth import get_user_model
from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view

from ngumpulyuk_app.common.openapi_params import path_str, q_int, q_str
from ngumpulyuk_app.common.openapi_responses import R200
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.views import APIView
from django.utils import timezone

from ngumpulyuk_app.authentication.serializers import user_me_dict, user_public_dict
from ngumpulyuk_app.common.api_response import err, ok
from ngumpulyuk_app.common.presenters import clamp_limit, clamp_offset, pagination_meta
from ngumpulyuk_app.communities.models import CommunityMember
from ngumpulyuk_app.events.models import Event, EventParticipant
from ngumpulyuk_app.users.interests import get_interest_popularity, get_interest_taxonomy
from ngumpulyuk_app.users.models import ActivityHistory, UserInterest, UserPreferences
from ngumpulyuk_app.users.serializers import (
    OnboardingSerializer,
    UserProfileUpdateSerializer,
    user_stats,
)

User = get_user_model()

USERS_TAG = ["Users"]


@extend_schema_view(
    get=extend_schema(tags=USERS_TAG, summary="Profil saya", responses=R200),
    put=extend_schema(
        tags=USERS_TAG,
        summary="Update profil saya",
        request=UserProfileUpdateSerializer,
        responses=R200,
    ),
)
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        u = request.user
        data = user_me_dict(u)
        data["stats"] = user_stats(u)
        return ok(data)

    def put(self, request):
        ser = UserProfileUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        u = request.user
        for k, v in ser.validated_data.items():
            setattr(u, k, v)
        u.save()
        data = user_me_dict(u)
        data["stats"] = user_stats(u)
        return ok(data)


@extend_schema_view(
    post=extend_schema(
        tags=USERS_TAG,
        summary="Selesaikan onboarding",
        request=OnboardingSerializer,
        responses=R200,
    ),
)
class OnboardingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = OnboardingSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        pd = ser.validated_data["personal_data"]
        u = request.user
        dob = pd["date_of_birth"]
        if isinstance(dob, str):
            u.date_of_birth = datetime.strptime(dob[:10], "%Y-%m-%d").date()
        else:
            u.date_of_birth = dob
        u.gender = pd["gender"]
        u.onboarding_completed = True
        pr = ser.validated_data.get("preferences")
        if pr is not None:
            loc = pr.get("preferred_location")
            if loc is not None and str(loc).strip():
                u.location = str(loc).strip()[:100]
        u.save()
        UserInterest.objects.filter(user=u).delete()
        for name in ser.validated_data["interests"]:
            UserInterest.objects.get_or_create(user=u, interest_name=name)
        pref_obj, _ = UserPreferences.objects.get_or_create(user=u)
        if pr is not None:
            pref_obj.preferred_days = pr.get("preferred_days")
            pref_obj.preferred_time = pr.get("preferred_time")
            pref_obj.preferred_location = pr.get("preferred_location")
        pref_obj.save()
        return ok({"onboarding_completed": True}, message="Onboarding completed")


@extend_schema_view(
    get=extend_schema(
        tags=USERS_TAG,
        summary="Profil publik by username",
        parameters=[path_str("username", "Username unik pengguna")],
        responses=R200,
    ),
)
class UserByUsernameView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, username):
        try:
            u = User.objects.get(username=username)
        except User.DoesNotExist:
            return err("NOT_FOUND", "User not found", status.HTTP_404_NOT_FOUND)
        data = user_public_dict(u)
        data["stats"] = user_stats(u)
        return ok(data)


@extend_schema_view(
    get=extend_schema(
        tags=USERS_TAG,
        summary="Riwayat aktivitas saya",
        parameters=[
            q_int("limit", "Jumlah item (default 20, max 100)", 20),
            q_int("offset", "Skip N item", 0),
        ],
        responses=R200,
    ),
)
class ActivityHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        passed_participants = (
            EventParticipant.objects.select_related("event")
            .filter(user=request.user, status="confirmed")
            .filter(
                Q(event__end_date__isnull=False, event__end_date__lt=today)
                | Q(event__end_date__isnull=True, event__event_date__lt=today)
            )
        )
        for participant in passed_participants:
            already_logged = ActivityHistory.objects.filter(
                user=request.user,
                activity_type="attended_event",
                related_type="event",
                related_id=participant.event_id,
            ).exists()
            if already_logged:
                continue
            ActivityHistory.objects.create(
                user=request.user,
                activity_type="attended_event",
                description=f"Attended event: {participant.event.title}",
                related_type="event",
                related_id=participant.event_id,
            )

        limit = clamp_limit(request.query_params.get("limit"), 20)
        offset = clamp_offset(request.query_params.get("offset"))
        qs = ActivityHistory.objects.filter(user=request.user).order_by("-created_at")
        total = qs.count()
        rows = qs[offset : offset + limit]
        activities = [
            {
                "id": str(a.id),
                "activity_type": a.activity_type,
                "description": a.description,
                "related_type": a.related_type,
                "related_id": str(a.related_id) if a.related_id else None,
                "created_at": a.created_at.isoformat().replace("+00:00", "Z"),
            }
            for a in rows
        ]
        return ok(
            {
                "activities": activities,
                **pagination_meta(total, limit, offset),
            }
        )


@extend_schema_view(
    get=extend_schema(
        tags=USERS_TAG,
        summary="Daftar ID event yang saya ikuti",
        responses=R200,
    ),
)
class JoinedEventIdsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        event_ids = list(
            EventParticipant.objects.filter(user=request.user, status="confirmed").values_list(
                "event_id", flat=True
            )
        )
        return ok({"event_ids": [str(event_id) for event_id in event_ids]})


@extend_schema_view(
    get=extend_schema(
        tags=USERS_TAG,
        summary="Ringkasan partisipasi pengguna",
        responses=R200,
    ),
)
class ParticipationSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        participant_qs = EventParticipant.objects.filter(user=request.user, status="confirmed").select_related(
            "event"
        )
        active_participants = participant_qs.filter(
            Q(event__end_date__isnull=False, event__end_date__gte=today)
            | Q(event__end_date__isnull=True, event__event_date__gte=today)
        ).order_by("event__event_date", "event__event_time")
        past_participants = participant_qs.filter(
            Q(event__end_date__isnull=False, event__end_date__lt=today)
            | Q(event__end_date__isnull=True, event__event_date__lt=today)
        ).order_by("-event__event_date", "-event__event_time")
        community_qs = CommunityMember.objects.filter(user=request.user).select_related("community").order_by(
            "-joined_at"
        )
        created_events_qs = Event.objects.filter(creator=request.user).order_by("-created_at")

        return ok(
            {
                "active_events_count": active_participants.count(),
                "past_events_count": past_participants.count(),
                "joined_communities_count": community_qs.count(),
                "events_created_count": created_events_qs.count(),
                "active_events": [
                    {
                        "id": str(p.event_id),
                        "title": p.event.title,
                        "status": p.event.status,
                        "joined_at": p.joined_at.isoformat().replace("+00:00", "Z"),
                    }
                    for p in active_participants
                ],
                "past_events": [
                    {
                        "id": str(p.event_id),
                        "title": p.event.title,
                        "status": p.event.status,
                        "joined_at": p.joined_at.isoformat().replace("+00:00", "Z"),
                    }
                    for p in past_participants
                ],
                "joined_communities": [
                    {
                        "id": str(m.community_id),
                        "title": m.community.name,
                        "joined_at": m.joined_at.isoformat().replace("+00:00", "Z"),
                    }
                    for m in community_qs
                ],
                "events_created": [
                    {
                        "id": str(ev.id),
                        "title": ev.title,
                        "status": ev.status,
                        "joined_at": ev.created_at.isoformat().replace("+00:00", "Z"),
                    }
                    for ev in created_events_qs
                ],
            }
        )


@extend_schema_view(
    get=extend_schema(
        tags=USERS_TAG,
        summary="Search user untuk blast admin",
        parameters=[
            q_str("search", "Cari by full_name / username / email"),
            q_int("limit", "Jumlah item (default 10, max 100)", 10),
            q_int("offset", "Skip N item", 0),
        ],
        responses=R200,
    ),
)
class AdminUserSearchView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        limit = clamp_limit(request.query_params.get("limit"), 10, max_val=100)
        offset = clamp_offset(request.query_params.get("offset"))
        search = (request.query_params.get("search") or "").strip()
        qs = User.objects.all().order_by("-created_at")
        if search:
            qs = qs.filter(
                Q(full_name__icontains=search)
                | Q(username__icontains=search)
                | Q(email__icontains=search)
            )
        count = qs.count()
        rows = qs[offset : offset + limit]
        results = [
            {
                "id": str(u.id),
                "full_name": u.full_name,
                "username": u.username,
                "email": u.email,
            }
            for u in rows
        ]
        return ok({"results": results, "count": count})


@extend_schema_view(
    get=extend_schema(
        tags=USERS_TAG,
        summary="Interest taxonomy (source of truth)",
        responses=R200,
    ),
)
class InterestTaxonomyView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        ranked = get_interest_popularity()
        return ok(
            {
                "interests": [row["interest"] for row in ranked],
                "ranked_interests": ranked,
                "total_interests": len(ranked),
                "ordering": "count_desc_then_interest_asc",
            }
        )
