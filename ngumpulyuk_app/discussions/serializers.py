from rest_framework import serializers


class CommentWriteSerializer(serializers.Serializer):
    content = serializers.CharField()
