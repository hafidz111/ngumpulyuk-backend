from rest_framework import serializers


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
    confirm = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Wajib "BLAST_ALL_USERS" jika all_users true.',
    )

    def validate(self, attrs):
        all_users = attrs.get("all_users")
        uids = attrs.get("user_ids") or []
        if all_users:
            if attrs.get("confirm") != "BLAST_ALL_USERS":
                raise serializers.ValidationError(
                    {"confirm": 'Set confirm to "BLAST_ALL_USERS" when all_users is true.'}
                )
        elif not uids:
            raise serializers.ValidationError(
                {"user_ids": "Provide a non-empty user_ids list, or set all_users with confirm."}
            )
        return attrs
