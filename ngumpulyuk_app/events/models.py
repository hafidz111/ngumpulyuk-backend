import uuid

from django.conf import settings
from django.db import models
from django.db.models import F


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_events",
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50)
    cover_image = models.CharField(max_length=255, blank=True, null=True)
    event_date = models.DateField()
    event_time = models.TimeField()
    end_date = models.DateField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    location_area = models.CharField(max_length=100)
    location_address = models.TextField()
    latitude = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)
    max_participants = models.PositiveIntegerField()
    current_participants = models.PositiveIntegerField(default=0)
    is_competition = models.BooleanField(default=False)
    difficulty_level = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ("beginner", "beginner"),
            ("intermediate", "intermediate"),
            ("advanced", "advanced"),
        ],
    )
    status = models.CharField(
        max_length=20,
        default="upcoming",
        choices=[
            ("upcoming", "upcoming"),
            ("ongoing", "ongoing"),
            ("completed", "completed"),
            ("cancelled", "cancelled"),
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "events"


class EventParticipant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="event_participations",
    )
    status = models.CharField(
        max_length=20,
        default="confirmed",
        choices=[
            ("confirmed", "confirmed"),
            ("waitlist", "waitlist"),
            ("cancelled", "cancelled"),
        ],
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    attendance_status = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[("attended", "attended"), ("no_show", "no_show")],
    )

    class Meta:
        db_table = "event_participants"
        unique_together = [["event", "user"]]

    def save(self, *args, **kwargs):
        from ngumpulyuk_app.users.models import ActivityHistory

        old_status = None
        if self.pk:
            old = EventParticipant.objects.filter(pk=self.pk).values("status").first()
            old_status = old["status"] if old else None
        super().save(*args, **kwargs)
        if old_status is None:
            if self.status == "confirmed":
                Event.objects.filter(pk=self.event_id).update(
                    current_participants=F("current_participants") + 1
                )
                title = Event.objects.filter(pk=self.event_id).values_list("title", flat=True).first() or ""
                ActivityHistory.objects.create(
                    user_id=self.user_id,
                    activity_type="joined_event",
                    description=f"Joined event: {title}",
                    related_type="event",
                    related_id=self.event_id,
                )
        else:
            if old_status == "confirmed" and self.status == "cancelled":
                Event.objects.filter(pk=self.event_id).update(
                    current_participants=F("current_participants") - 1
                )
            elif old_status != "confirmed" and self.status == "confirmed":
                Event.objects.filter(pk=self.event_id).update(
                    current_participants=F("current_participants") + 1
                )
                title = Event.objects.filter(pk=self.event_id).values_list("title", flat=True).first() or ""
                ActivityHistory.objects.create(
                    user_id=self.user_id,
                    activity_type="joined_event",
                    description=f"Joined event: {title}",
                    related_type="event",
                    related_id=self.event_id,
                )

    def delete(self, *args, **kwargs):
        was_confirmed = self.status == "confirmed"
        eid = self.event_id
        super().delete(*args, **kwargs)
        if was_confirmed:
            Event.objects.filter(pk=eid).update(current_participants=F("current_participants") - 1)


class EventTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tags")
    tag_name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "event_tags"
