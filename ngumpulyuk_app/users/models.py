import uuid

from django.conf import settings
from django.db import models


class UserPreferences(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preferences_row",
    )
    preferred_days = models.JSONField(blank=True, null=True)
    preferred_time = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ("morning", "morning"),
            ("afternoon", "afternoon"),
            ("evening", "evening"),
            ("night", "night"),
        ],
    )
    preferred_location = models.CharField(max_length=100, blank=True, null=True)
    notification_enabled = models.BooleanField(default=True)
    email_notification = models.BooleanField(default=True)
    push_notification = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_preferences"


class UserInterest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="interest_rows",
    )
    interest_name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_interests"
        unique_together = [["user", "interest_name"]]


class ActivityHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activity_history",
    )
    activity_type = models.CharField(
        max_length=50,
        choices=[
            ("joined_event", "joined_event"),
            ("attended_event", "attended_event"),
            ("created_event", "created_event"),
            ("joined_community", "joined_community"),
            ("left_community", "left_community"),
            ("created_community", "created_community"),
            ("posted_thread", "posted_thread"),
            ("commented", "commented"),
        ],
    )
    description = models.TextField()
    related_type = models.CharField(max_length=50, blank=True, null=True)
    related_id = models.UUIDField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "activity_history"
        verbose_name_plural = "activity histories"
