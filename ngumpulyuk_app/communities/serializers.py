from rest_framework import serializers


class CommunityWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    description = serializers.CharField()
    category = serializers.CharField(max_length=50)
    cover_image = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    logo = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)


class ThreadWriteSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200, required=False, allow_blank=True)
    content = serializers.CharField()
    images = serializers.ListField(child=serializers.CharField(), required=False)
