from datetime import datetime

from rest_framework import serializers

from ngumpulyuk_app.common.presenters import mini_user
from ngumpulyuk_app.events.models import Event, EventParticipant


def event_list_item(ev):
    tags = list(ev.tags.values_list("tag_name", flat=True))
    creator = ev.creator
    return {
        "id": str(ev.id),
        "title": ev.title,
        "description": ev.description,
        "category": ev.category,
        "cover_image": ev.cover_image,
        "event_date": ev.event_date.isoformat(),
        "event_time": ev.event_time.strftime("%H:%M:%S") if ev.event_time else None,
        "location_area": ev.location_area,
        "location_address": ev.location_address,
        "max_participants": ev.max_participants,
        "current_participants": ev.current_participants,
        "status": ev.status,
        "creator": mini_user(creator),
        "tags": tags,
        "created_at": ev.created_at.isoformat().replace("+00:00", "Z") if ev.created_at else None,
    }


def event_detail(ev, request_user=None):
    tags = list(ev.tags.values_list("tag_name", flat=True))
    participants_qs = (
        EventParticipant.objects.filter(event=ev, status="confirmed")
        .select_related("user")
        .order_by("joined_at")
    )
    participants = [mini_user(p.user) for p in participants_qs]
    is_joined = False
    if request_user and request_user.is_authenticated:
        is_joined = EventParticipant.objects.filter(
            event=ev, user=request_user, status="confirmed"
        ).exists()
    c = ev.creator
    return {
        "id": str(ev.id),
        "title": ev.title,
        "description": ev.description,
        "category": ev.category,
        "cover_image": ev.cover_image,
        "event_date": ev.event_date.isoformat(),
        "event_time": ev.event_time.strftime("%H:%M:%S") if ev.event_time else None,
        "location_area": ev.location_area,
        "location_address": ev.location_address,
        "latitude": float(ev.latitude) if ev.latitude is not None else None,
        "longitude": float(ev.longitude) if ev.longitude is not None else None,
        "max_participants": ev.max_participants,
        "current_participants": ev.current_participants,
        "is_competition": ev.is_competition,
        "difficulty_level": ev.difficulty_level,
        "status": ev.status,
        "creator": {
            "id": str(c.id),
            "username": c.username,
            "full_name": c.full_name,
            "profile_picture": c.profile_picture,
            "bio": c.bio,
        },
        "tags": tags,
        "participants": participants,
        "is_joined": is_joined,
        "created_at": ev.created_at.isoformat().replace("+00:00", "Z") if ev.created_at else None,
        "updated_at": ev.updated_at.isoformat().replace("+00:00", "Z") if ev.updated_at else None,
    }


class EventWriteSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField()
    category = serializers.CharField(max_length=50)
    cover_image = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    event_date = serializers.DateField()
    event_time = serializers.CharField()
    location_area = serializers.CharField(max_length=100)
    location_address = serializers.CharField()
    latitude = serializers.DecimalField(max_digits=10, decimal_places=8, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=11, decimal_places=8, required=False, allow_null=True)
    max_participants = serializers.IntegerField(min_value=1)
    is_competition = serializers.BooleanField(required=False, default=False)
    difficulty_level = serializers.ChoiceField(
        choices=["beginner", "intermediate", "advanced"], required=False, allow_null=True
    )
    tags = serializers.ListField(child=serializers.CharField(max_length=50), required=False)

    def parse_time(self, s):
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(s.strip(), fmt).time()
            except ValueError:
                continue
        raise serializers.ValidationError({"event_time": "Invalid time format"})
