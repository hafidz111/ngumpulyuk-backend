"""
Firebase Cloud Messaging (HTTP v1 via firebase-admin).

Set FIREBASE_CREDENTIALS_PATH in settings to the service account JSON path.
If unset, push is skipped (in-app notifications still work).
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ngumpulyuk_app.authentication.models import User


def _ensure_app() -> bool:
    """Return True if Firebase app is ready."""
    from pathlib import Path

    from django.conf import settings

    import firebase_admin
    from firebase_admin import credentials

    try:
        firebase_admin.get_app()
        return True
    except ValueError:
        pass

    path = getattr(settings, "FIREBASE_CREDENTIALS_PATH", None)
    if not path:
        return False
    p = Path(path)
    if not p.is_file():
        logger.warning("FIREBASE_CREDENTIALS_PATH is set but file not found: %s", path)
        return False
    cred = credentials.Certificate(str(p))
    firebase_admin.initialize_app(cred)
    return True


def send_fcm_to_user(
    user: User,
    *,
    title: str,
    body: str,
    link_url: str | None = None,
) -> None:
    """
    Send data + notification payload to all registered FCM tokens for this user.
    Removes tokens that FCM reports as invalid/unregistered.
    """
    if not _ensure_app():
        logger.debug("FCM not configured; skip push for user=%s", user.id)
        return

    from firebase_admin import exceptions, messaging

    from ngumpulyuk_app.notifications.models import PushDevice

    tokens = list(PushDevice.objects.filter(user_id=user.id).values_list("token", flat=True))
    if not tokens:
        return

    data = {"link_url": link_url or ""}
    messages = []
    for t in tokens:
        messages.append(
            messaging.Message(
                notification=messaging.Notification(title=title[:200], body=body[:500]),
                data={k: str(v) for k, v in data.items()},
                token=t,
            )
        )

    try:
        batch = messaging.send_each(messages)
    except exceptions.FirebaseError as e:
        logger.exception("FCM send_each failed: %s", e)
        return

    for idx, send_resp in enumerate(batch.responses):
        if send_resp.success:
            continue
        exc = send_resp.exception
        token = tokens[idx]
        if exc is None:
            continue
        err_str = str(exc).lower()
        if any(
            x in err_str
            for x in (
                "not found",
                "unregistered",
                "invalid registration",
                "requested entity was not found",
                "registration-token-not-registered",
            )
        ):
            PushDevice.objects.filter(token=token).delete()
            logger.info("Removed invalid FCM token: %s", exc)
            continue
        logger.warning("FCM send failed for token …%s: %s", token[-8:], exc)
