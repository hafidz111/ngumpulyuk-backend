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
