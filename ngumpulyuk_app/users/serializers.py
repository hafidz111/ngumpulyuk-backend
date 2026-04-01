from rest_framework import serializers


def user_stats(user):
    from ngumpulyuk_app.communities.models import CommunityMember
    from ngumpulyuk_app.events.models import Event, EventParticipant

    events_joined = EventParticipant.objects.filter(user=user, status="confirmed").count()
    events_created = Event.objects.filter(creator=user).count()
    communities_joined = CommunityMember.objects.filter(user=user).count()
    return {
        "events_joined": events_joined,
        "events_created": events_created,
        "communities_joined": communities_joined,
    }


class OnboardingSerializer(serializers.Serializer):
    personal_data = serializers.DictField()
    interests = serializers.ListField(child=serializers.CharField(max_length=50))
    preferences = serializers.DictField()

    def validate_personal_data(self, v):
        dob = v.get("date_of_birth")
        gender = v.get("gender")
        if not dob or not gender:
            raise serializers.ValidationError("date_of_birth and gender are required")
        if gender not in ("male", "female", "other"):
            raise serializers.ValidationError("Invalid gender")
        return v


class UserProfileUpdateSerializer(serializers.Serializer):
    """Profil umum; date_of_birth & gender hanya lewat POST /users/onboarding."""

    full_name = serializers.CharField(max_length=100, required=False)
    bio = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    location = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        initial = getattr(self, "initial_data", None) or {}
        blocked = {"date_of_birth", "gender"} & set(initial.keys())
        if blocked:
            raise serializers.ValidationError(
                {k: "Hanya bisa diisi lewat onboarding (POST /users/onboarding)." for k in sorted(blocked)}
            )
        return attrs
