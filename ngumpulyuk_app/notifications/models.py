import uuid

from django.conf import settings
from django.db import models


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(
        max_length=50,
        choices=[
            ("event_reminder", "event_reminder"),
            ("new_event", "new_event"),
            ("event_update", "event_update"),
            ("community_post", "community_post"),
            ("comment_reply", "comment_reply"),
            ("new_member", "new_member"),
            ("event_full", "event_full"),
            ("admin_broadcast", "admin_broadcast"),
        ],
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    link_url = models.CharField(max_length=255, blank=True, null=True)
    related_id = models.UUIDField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"


class PushDevice(models.Model):
    """FCM registration tokens per user (multiple devices)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="push_devices",
    )
    token = models.CharField(max_length=512, unique=True, db_index=True)
    platform = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ("android", "android"),
            ("ios", "ios"),
            ("web", "web"),
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "push_devices"


class BlastNotificationAudit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blast_notification_audits",
    )
    title = models.CharField(max_length=200)
    target_mode = models.CharField(
        max_length=30,
        choices=[
            ("user_ids", "user_ids"),
            ("all_users", "all_users"),
            ("interests", "interests"),
        ],
    )
    target_count = models.PositiveIntegerField(default=0)
    queued_count = models.PositiveIntegerField(default=0)
    skipped_count = models.PositiveIntegerField(default=0)
    payload_summary = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "blast_notification_audits"
