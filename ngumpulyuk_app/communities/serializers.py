from rest_framework import serializers
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError as DjangoValidationError


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

    def validate_images(self, value):
        if value is None:
            return []
        if len(value) > 3:
            raise serializers.ValidationError(
                {"code": "THREAD_IMAGE_LIMIT_EXCEEDED", "message": "Maksimal 3 gambar per thread."}
            )
        validator = URLValidator()
        for image_url in value:
            try:
                validator(image_url)
            except DjangoValidationError:
                raise serializers.ValidationError(
                    {"code": "INVALID_IMAGE_URL", "message": "Setiap item images harus URL valid."}
                )
        return value
