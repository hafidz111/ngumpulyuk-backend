from datetime import datetime

from rest_framework import serializers

from ngumpulyuk_app.common.presenters import mini_user
from ngumpulyuk_app.events.models import Event, EventParticipant


def _event_tag_names(ev):
    prefetched = getattr(ev, "_prefetched_objects_cache", None)
    if prefetched is not None and "tags" in prefetched:
        return [t.tag_name for t in ev.tags.all()]
    return list(ev.tags.values_list("tag_name", flat=True))


def event_list_item(ev, is_joined=False):
    tags = _event_tag_names(ev)
    creator = ev.creator
    return {
        "id": str(ev.id),
        "title": ev.title,
        "category": ev.category,
        "cover_image": ev.cover_image,
        "event_date": ev.event_date.isoformat(),
        "event_time": ev.event_time.strftime("%H:%M:%S") if ev.event_time else None,
        "end_date": ev.end_date.isoformat() if ev.end_date else None,
        "end_time": ev.end_time.strftime("%H:%M:%S") if ev.end_time else None,
        "has_registration_deadline": ev.has_registration_deadline,
        "registration_deadline": ev.registration_deadline.isoformat() if ev.registration_deadline else None,
        "registration_deadline_time": (
            ev.registration_deadline_time.strftime("%H:%M:%S") if ev.registration_deadline_time else None
        ),
        "location_area": ev.location_area,
        "location_address": ev.location_address,
        "latitude": float(ev.latitude) if ev.latitude is not None else None,
        "longitude": float(ev.longitude) if ev.longitude is not None else None,
        "max_participants": ev.max_participants,
        "participant_count": ev.current_participants,
        "status": ev.status,
        "difficulty_level": ev.difficulty_level,
        "is_competition": ev.is_competition,
        "creator": mini_user(creator),
        "tags": tags,
        "is_joined": is_joined,
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
        "end_date": ev.end_date.isoformat() if ev.end_date else None,
        "end_time": ev.end_time.strftime("%H:%M:%S") if ev.end_time else None,
        "has_registration_deadline": ev.has_registration_deadline,
        "registration_deadline": ev.registration_deadline.isoformat() if ev.registration_deadline else None,
        "registration_deadline_time": (
            ev.registration_deadline_time.strftime("%H:%M:%S") if ev.registration_deadline_time else None
        ),
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
    end_date = serializers.DateField(required=False, allow_null=True)
    end_time = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    has_registration_deadline = serializers.BooleanField(required=False, default=False)
    registration_deadline = serializers.DateField(required=False, allow_null=True)
    registration_deadline_time = serializers.CharField(required=False, allow_null=True, allow_blank=True)
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

    def parse_time(self, s, field_name="event_time"):
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(s.strip(), fmt).time()
            except ValueError:
                continue
        raise serializers.ValidationError({field_name: "Invalid time format"})

    def validate(self, attrs):
        event_date = attrs.get("event_date")
        has_registration_deadline = attrs.get("has_registration_deadline", False)
        registration_deadline = attrs.get("registration_deadline")
        registration_deadline_time = attrs.get("registration_deadline_time")
        if not has_registration_deadline:
            if event_date is not None:
                attrs["registration_deadline"] = event_date
                attrs["registration_deadline_time"] = None
                registration_deadline = event_date
                registration_deadline_time = None
        elif registration_deadline is None and event_date is not None:
            attrs["registration_deadline"] = event_date
            registration_deadline = event_date
        if registration_deadline and event_date and registration_deadline > event_date:
            raise serializers.ValidationError(
                {"registration_deadline": "Registration deadline cannot be after event date"}
            )
        event_time = attrs.get("event_time")
        if (
            registration_deadline
            and event_date
            and registration_deadline == event_date
            and registration_deadline_time
            and event_time
        ):
            parsed_deadline_time = self.parse_time(
                registration_deadline_time, "registration_deadline_time"
            )
            parsed_event_time = self.parse_time(event_time, "event_time")
            if parsed_deadline_time > parsed_event_time:
                raise serializers.ValidationError(
                    {
                        "registration_deadline_time": (
                            "Registration deadline time cannot be after event time "
                            "when deadline date equals event date"
                        )
                    }
                )
        return attrs
