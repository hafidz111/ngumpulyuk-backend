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


class OnboardingPersonalSerializer(serializers.Serializer):
    date_of_birth = serializers.DateField()
    gender = serializers.ChoiceField(choices=["male", "female", "other"])


class OnboardingPreferencesSerializer(serializers.Serializer):
    preferred_days = serializers.ListField(child=serializers.CharField(), required=False)
    preferred_time = serializers.ChoiceField(
        choices=["morning", "afternoon", "evening", "night"],
        required=False,
        allow_null=True,
    )
    preferred_location = serializers.CharField(
        max_length=100, required=False, allow_blank=True, allow_null=True
    )


class OnboardingSerializer(serializers.Serializer):
    personal_data = OnboardingPersonalSerializer()
    interests = serializers.ListField(child=serializers.CharField(max_length=50))
    preferences = OnboardingPreferencesSerializer(required=False)


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
