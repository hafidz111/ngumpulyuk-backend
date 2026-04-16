import uuid

from django.conf import settings
from django.db import models


class ChatTurn(models.Model):
    """
    Metrik & feedback per jawaban. Tidak menyimpan isi pesan user (hanya hash redaksi).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_turns",
    )
    session_key = models.CharField(max_length=64, blank=True, default="")
    intent = models.CharField(max_length=32)
    prompt_sha256 = models.CharField(max_length=64, blank=True, default="")
    prompt_length = models.PositiveIntegerField(default=0)
    user_message_redacted = models.TextField(blank=True, default="")
    assistant_reply = models.TextField(blank=True, default="")
    cards_json = models.JSONField(default=list, blank=True)
    sources_json = models.JSONField(default=list, blank=True)
    llm_used = models.BooleanField(default=False)
    correction_applied = models.BooleanField(default=False)
    card_event_count = models.PositiveSmallIntegerField(default=0)
    card_community_count = models.PositiveSmallIntegerField(default=0)
    card_area_count = models.PositiveSmallIntegerField(default=0)
    helpful = models.BooleanField(null=True, blank=True)
    feedback_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_turns"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["intent", "-created_at"]),
        ]


class ChatAnswerCorrection(models.Model):
    """
    Admin-curated corrected answers to prevent repeated wrong outputs.
    Match rule: exact normalized query text (redacted).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    normalized_query = models.CharField(max_length=500, unique=True)
    corrected_reply = models.TextField()
    source_type = models.CharField(max_length=16, default="manual")
    source_ref = models.CharField(max_length=100, blank=True, default="")
    intent = models.CharField(max_length=32, blank=True, default="")
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default="")
    usage_count = models.PositiveIntegerField(default=0)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="chat_corrections_created",
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="chat_corrections_updated",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "chat_answer_corrections"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["is_active", "-updated_at"]),
            models.Index(fields=["intent", "-updated_at"]),
        ]
