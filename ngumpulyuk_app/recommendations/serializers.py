from rest_framework import serializers


class RecommendationSignalWriteSerializer(serializers.Serializer):
    event_id = serializers.UUIDField()
    signal_type = serializers.ChoiceField(
        choices=["view", "like", "join", "save", "share", "dislike"]
    )
    value = serializers.DecimalField(max_digits=7, decimal_places=2, required=False)
    dwell_ms = serializers.IntegerField(required=False, min_value=0)
    platform = serializers.ChoiceField(
        choices=["android", "ios", "web"],
        required=False,
        allow_null=True,
    )
    source = serializers.CharField(max_length=50, required=False, allow_blank=True)
