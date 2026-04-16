from rest_framework import serializers

from ngumpulyuk_app.users.interests import get_interest_taxonomy, normalize_interest


class FCMDeviceRegisterSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=512, min_length=10)
    platform = serializers.ChoiceField(
        choices=["android", "ios", "web"],
        required=False,
        allow_null=True,
    )


class FCMDeviceDeleteSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=512, min_length=10)


class BlastNotificationSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    message = serializers.CharField(max_length=8000)
    link_url = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    all_users = serializers.BooleanField(default=False)
    user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
    )
    interests = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=True,
        help_text="Interest slug list, e.g. running,yoga,cycling",
    )
    confirm = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Wajib "BLAST_ALL_USERS" jika all_users true.',
    )

    def validate(self, attrs):
        all_users = attrs.get("all_users", False)
        uids = attrs.get("user_ids") or []
        interests = attrs.get("interests") or []

        modes_selected = int(bool(uids)) + int(bool(all_users)) + int(bool(interests))
        if modes_selected != 1:
            raise serializers.ValidationError(
                "Choose exactly one target mode: user_ids OR all_users OR interests."
            )

        if all_users:
            if attrs.get("confirm") != "BLAST_ALL_USERS":
                raise serializers.ValidationError(
                    {"confirm": 'Set confirm to "BLAST_ALL_USERS" when all_users is true.'}
                )
            attrs["target_mode"] = "all_users"
            return attrs

        if uids:
            attrs["target_mode"] = "user_ids"
            return attrs

        taxonomy = set(get_interest_taxonomy())
        normalized = [normalize_interest(v) for v in interests if normalize_interest(v)]
        if not normalized:
            raise serializers.ValidationError({"interests": "Provide at least one interest slug."})
        invalid = sorted([v for v in normalized if v not in taxonomy])
        if invalid:
            raise serializers.ValidationError(
                {
                    "interests": (
                        "Invalid interest value(s): "
                        + ", ".join(invalid)
                        + ". Use values from GET /api/v1/users/interests/."
                    )
                }
            )
        attrs["interests"] = normalized
        attrs["target_mode"] = "interests"
        return attrs
