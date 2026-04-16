"""
Application-layer helpers for in-app notifications and future email/push hooks.
"""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Iterable, Sequence

from django.utils import timezone

from ngumpulyuk_app.notifications.models import Notification
from ngumpulyuk_app.users.models import UserPreferences

if TYPE_CHECKING:
    from ngumpulyuk_app.authentication.models import User

logger = logging.getLogger(__name__)

DEFAULT_DEDUP_WINDOW_SECONDS = 3600


def get_user_preferences(user: User) -> UserPreferences | None:
    return UserPreferences.objects.filter(user_id=user.id).first()


def accepts_in_app_notifications(user: User) -> bool:
    pref = get_user_preferences(user)
    if pref is None:
        return True
    return pref.notification_enabled


def dispatch_side_channels(
    user: User,
    *,
    title: str,
    message: str,
    link_url: str | None,
) -> None:
    """
    Respect email_notification / push_notification.
    Push: Firebase Cloud Messaging when FIREBASE_CREDENTIALS_PATH is configured.
    Email: still a stub until SES/SMTP batch is wired here.
    """
    pref = get_user_preferences(user)
    if pref and not pref.notification_enabled:
        return
    email_on = pref.email_notification if pref else True
    push_on = pref.push_notification if pref else True

    if email_on:
        logger.debug("email_notification stub: user=%s title=%s", user.id, title)
    if push_on:
        from ngumpulyuk_app.notifications.fcm import send_fcm_to_user

        send_fcm_to_user(user, title=title, body=message, link_url=link_url)


def _should_skip_duplicate(
    *,
    user: User,
    ntype: str,
    related_id,
    dedupe_exact_related: bool,
    dedup_window_seconds: int | None,
) -> bool:
    qs = Notification.objects.filter(user=user, type=ntype)
    if related_id is not None:
        qs = qs.filter(related_id=related_id)
    else:
        qs = qs.filter(related_id__isnull=True)

    if dedupe_exact_related and related_id is not None:
        return qs.exists()

    if dedup_window_seconds is not None and related_id is not None:
        since = timezone.now() - timedelta(seconds=dedup_window_seconds)
        return qs.filter(created_at__gte=since).exists()

    return False


def create_notification(
    user: User,
    ntype: str,
    *,
    title: str,
    message: str,
    link_url: str | None = None,
    related_id=None,
    dedupe_exact_related: bool = False,
    dedup_window_seconds: int | None = None,
    send_side_channels: bool = True,
) -> Notification | None:
    """
    Single entry point for creating Notification rows.

    dedupe_exact_related: if True, skip when any row exists with same user+type+related_id
      (used for event_reminder once per event per user).
    dedup_window_seconds: skip duplicate within time window (same user+type+related_id).
    """
    if not accepts_in_app_notifications(user):
        return None

    if _should_skip_duplicate(
        user=user,
        ntype=ntype,
        related_id=related_id,
        dedupe_exact_related=dedupe_exact_related,
        dedup_window_seconds=dedup_window_seconds,
    ):
        return None

    n = Notification.objects.create(
        user=user,
        type=ntype,
        title=title,
        message=message,
        link_url=link_url or None,
        related_id=related_id,
    )
    if send_side_channels:
        dispatch_side_channels(user, title=title, message=message, link_url=link_url)
    return n


def create_notifications_bulk(
    users: Iterable[User],
    ntype: str,
    *,
    title: str,
    message: str,
    link_url: str | None = None,
    related_id=None,
    exclude_user_ids: Sequence | None = None,
    existing_pairs: set[tuple] | None = None,
) -> int:
    """
    Bulk in-app notifications. Skips users with notification_enabled=False.
    existing_pairs: optional set of (user_id, related_id) already notified for this batch
      to avoid duplicates when callers iterate carefully.
    """
    exclude = set(exclude_user_ids or [])
    pairs = existing_pairs if existing_pairs is not None else set()
    rows: list[Notification] = []
    for user in users:
        if user.id in exclude:
            continue
        if not accepts_in_app_notifications(user):
            continue
        key = (user.id, related_id)
        if key in pairs:
            continue
        if related_id is not None:
            if Notification.objects.filter(
                user_id=user.id, type=ntype, related_id=related_id
            ).exists():
                continue
        pairs.add(key)
        rows.append(
            Notification(
                user=user,
                type=ntype,
                title=title,
                message=message,
                link_url=link_url or None,
                related_id=related_id,
            )
        )
    if not rows:
        return 0
    Notification.objects.bulk_create(rows)
    for n in rows:
        dispatch_side_channels(n.user, title=title, message=message, link_url=link_url)
    return len(rows)


def blast_admin_notifications(
    *,
    title: str,
    message: str,
    link_url: str | None = None,
    user_ids: list | None = None,
    all_users: bool = False,
) -> int:
    """
    Staff-only: create admin_broadcast notifications + FCM for each target user.
    Processes in chunks to limit memory. Skips users with notification_enabled=False via bulk_create path.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    total = 0
    chunk: list = []
    chunk_size = 300

    if all_users:
        qs = User.objects.filter(is_active=True).order_by("id")
    else:
        qs = User.objects.filter(is_active=True, id__in=(user_ids or [])).order_by("id")

    for user in qs.iterator(chunk_size=chunk_size):
        chunk.append(user)
        if len(chunk) >= chunk_size:
            total += create_notifications_bulk(
                chunk,
                "admin_broadcast",
                title=title,
                message=message,
                link_url=link_url,
                related_id=None,
            )
            chunk = []
    if chunk:
        total += create_notifications_bulk(
            chunk,
            "admin_broadcast",
            title=title,
            message=message,
            link_url=link_url,
            related_id=None,
        )
    return total
