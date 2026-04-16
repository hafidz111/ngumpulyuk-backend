import uuid

from django.conf import settings
from django.db import models

from ngumpulyuk_app.events.models import Event


class AiRecommendation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_recommendations",
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="ai_recommendations")
    score = models.DecimalField(max_digits=5, decimal_places=2)
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "ai_recommendations"


class RecommendationSignal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recommendation_signals",
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="recommendation_signals")
    signal_type = models.CharField(
        max_length=30,
        choices=[
            ("view", "view"),
            ("like", "like"),
            ("join", "join"),
            ("save", "save"),
            ("share", "share"),
            ("dislike", "dislike"),
        ],
    )
    value = models.DecimalField(max_digits=7, decimal_places=2, default=1)
    dwell_ms = models.PositiveIntegerField(blank=True, null=True)
    platform = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[("android", "android"), ("ios", "ios"), ("web", "web")],
    )
    source = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "recommendation_signals"
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["event", "created_at"]),
            models.Index(fields=["user", "event"]),
            models.Index(fields=["signal_type", "created_at"]),
        ]
