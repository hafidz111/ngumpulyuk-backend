from __future__ import annotations

import re
from typing import Optional

from django.db.models import F
from django.utils import timezone

from ngumpulyuk_app.chat.models import ChatAnswerCorrection


_WS_RE = re.compile(r"\s+")


def normalize_query(text: str) -> str:
    s = (text or "").strip().lower()
    s = _WS_RE.sub(" ", s)
    return s[:500]


def find_correction(*, redacted_message: str, intent: str) -> Optional[ChatAnswerCorrection]:
    normalized = normalize_query(redacted_message)
    if not normalized:
        return None
    row = (
        ChatAnswerCorrection.objects.filter(
            normalized_query=normalized,
            is_active=True,
            intent=intent,
        ).order_by("-updated_at").first()
    )
    if row:
        return row
    return (
        ChatAnswerCorrection.objects.filter(
            normalized_query=normalized,
            is_active=True,
            intent="",
        )
        .order_by("-updated_at")
        .first()
    ) or (
        ChatAnswerCorrection.objects.filter(
            normalized_query=normalized,
            is_active=True,
        )
        .order_by("-updated_at")
        .first()
    )


def mark_correction_used(correction: ChatAnswerCorrection) -> None:
    ChatAnswerCorrection.objects.filter(pk=correction.pk).update(
        usage_count=F("usage_count") + 1,
        last_used_at=timezone.now(),
    )
