from datetime import datetime

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from ngumpulyuk_app.authentication.serializers import user_me_dict, user_public_dict
from ngumpulyuk_app.common.api_response import err, ok
from ngumpulyuk_app.common.presenters import clamp_limit, clamp_offset, pagination_meta
from ngumpulyuk_app.users.models import ActivityHistory, UserInterest, UserPreferences
from ngumpulyuk_app.users.serializers import (
    OnboardingSerializer,
    UserProfileUpdateSerializer,
    user_stats,
)

User = get_user_model()

USERS_TAG = ["Users"]


@extend_schema_view(
    get=extend_schema(tags=USERS_TAG, summary="Profil saya (GET)"),
    put=extend_schema(tags=USERS_TAG, summary="Update profil saya (PUT)"),
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
    post=extend_schema(tags=USERS_TAG, summary="Selesaikan onboarding"),
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
        u.save()
        UserInterest.objects.filter(user=u).delete()
        for name in ser.validated_data["interests"]:
            UserInterest.objects.get_or_create(user=u, interest_name=name)
        prefs = ser.validated_data["preferences"]
        pref_obj, _ = UserPreferences.objects.get_or_create(user=u)
        pref_obj.preferred_days = prefs.get("preferred_days")
        pref_obj.preferred_time = prefs.get("preferred_time")
        pref_obj.preferred_location = prefs.get("preferred_location")
        pref_obj.save()
        return ok({"onboarding_completed": True}, message="Onboarding completed")


@extend_schema_view(
    get=extend_schema(tags=USERS_TAG, summary="Profil publik by username"),
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
    get=extend_schema(tags=USERS_TAG, summary="Riwayat aktivitas saya"),
)
class ActivityHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
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
