"""
Domain notification triggers — call from views after successful writes.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from django.contrib.auth import get_user_model

from ngumpulyuk_app.communities.models import Community, CommunityMember
from ngumpulyuk_app.events.models import Event, EventParticipant
from ngumpulyuk_app.notifications import services
from ngumpulyuk_app.discussions.models import Comment, Thread

User = get_user_model()


def event_start_datetime(ev: Event) -> datetime:
    dt = datetime.combine(ev.event_date, ev.event_time)
    from django.utils import timezone as dj_tz

    if dj_tz.is_naive(dt):
        dt = dj_tz.make_aware(dt, dj_tz.get_current_timezone())
    return dt


def _event_link(ev: Event) -> str:
    return f"/events/{ev.id}"


def _community_link(c: Community) -> str:
    return f"/communities/{c.id}"


def _thread_link(t: Thread) -> str:
    return f"/threads/{t.id}"


def notify_new_event(ev: Event) -> int:
    """
    Notify users who joined other events hosted by the same creator (repeat audience).
    """
    attendee_ids = (
        EventParticipant.objects.filter(event__creator_id=ev.creator_id, status="confirmed")
        .exclude(user_id=ev.creator_id)
        .exclude(event_id=ev.id)
        .values_list("user_id", flat=True)
        .distinct()
    )
    users = User.objects.filter(id__in=attendee_ids)
    title = "Acara baru"
    message = f"{ev.creator.full_name} membuat acara: {ev.title}"
    return services.create_notifications_bulk(
        users,
        "new_event",
        title=title,
        message=message,
        link_url=_event_link(ev),
        related_id=ev.id,
    )


def notify_event_updated(ev: Event, *, editor_id, old_snapshot: tuple, new_snapshot: tuple) -> None:
    if old_snapshot == new_snapshot:
        return
    participants = (
        EventParticipant.objects.filter(event=ev, status="confirmed")
        .exclude(user_id=editor_id)
        .select_related("user")
    )
    title = "Acara diperbarui"
    message = f"Detail acara \"{ev.title}\" telah diubah."
    for ep in participants:
        services.create_notification(
            ep.user,
            "event_update",
            title=title,
            message=message,
            link_url=_event_link(ev),
            related_id=ev.id,
            dedup_window_seconds=services.DEFAULT_DEDUP_WINDOW_SECONDS,
        )


def snapshot_event(ev: Event) -> tuple:
    return (
        ev.title,
        ev.description,
        ev.category,
        ev.event_date,
        ev.event_time,
        ev.end_date,
        ev.end_time,
        ev.location_area,
        ev.location_address,
        ev.max_participants,
        ev.status,
        ev.has_registration_deadline,
        ev.registration_deadline,
        ev.registration_deadline_time,
    )


def notify_event_full(ev: Event) -> None:
    participants = EventParticipant.objects.filter(event=ev, status="confirmed").select_related("user")
    title = "Acara penuh"
    message = f"Kuota peserta \"{ev.title}\" sudah terpenuhi."
    for ep in participants:
        services.create_notification(
            ep.user,
            "event_full",
            title=title,
            message=message,
            link_url=_event_link(ev),
            related_id=ev.id,
            dedup_window_seconds=services.DEFAULT_DEDUP_WINDOW_SECONDS,
        )


def notify_community_new_thread(thread: Thread, community: Community) -> None:
    member_users = (
        User.objects.filter(
            community_memberships__community_id=community.id,
        )
        .exclude(id=thread.author_id)
        .distinct()
    )
    label = (thread.title or "").strip() or "Postingan baru"
    title = "Posting di komunitas"
    message = f"{thread.author.full_name} menulis di {community.name}: {label[:120]}"
    services.create_notifications_bulk(
        member_users,
        "community_post",
        title=title,
        message=message,
        link_url=_thread_link(thread),
        related_id=thread.id,
    )


def notify_thread_new_comment(comment: Comment, thread: Thread) -> None:
    if thread.author_id == comment.author_id:
        return
    title = "Komentar baru"
    label = (thread.title or "").strip() or "thread"
    message = f"{comment.author.full_name} mengomentari \"{label[:80]}\"."
    services.create_notification(
        thread.author,
        "comment_reply",
        title=title,
        message=message,
        link_url=_thread_link(thread),
        related_id=thread.id,
        dedup_window_seconds=120,
    )


def notify_community_new_member(community: Community, *, new_member: User) -> None:
    recipient_ids = {community.creator_id}
    recipient_ids.update(
        CommunityMember.objects.filter(
            community=community, role__in=["admin", "moderator"]
        ).values_list("user_id", flat=True)
    )
    recipient_ids.discard(new_member.id)
    users = User.objects.filter(id__in=recipient_ids)
    title = "Anggota baru"
    message = f"{new_member.full_name} bergabung ke {community.name}."
    services.create_notifications_bulk(
        users,
        "new_member",
        title=title,
        message=message,
        link_url=_community_link(community),
        related_id=community.id,
    )


def send_event_reminders_for_window() -> int:
    """
    For events starting in ~24 hours (23–25h window), remind confirmed participants once.
    Intended to be run hourly via cron.
    """
    from django.utils import timezone as dj_tz

    now = dj_tz.now()
    created = 0
    upcoming = Event.objects.filter(status="upcoming")
    for ev in upcoming.iterator():
        start = event_start_datetime(ev)
        if start <= now:
            continue
        remaining = start - now
        if not (timedelta(hours=23) <= remaining <= timedelta(hours=25)):
            continue
        for ep in EventParticipant.objects.filter(event=ev, status="confirmed").select_related("user"):
            n = services.create_notification(
                ep.user,
                "event_reminder",
                title="Pengingat acara",
                message=f"\"{ev.title}\" dimulai dalam sekitar 24 jam.",
                link_url=_event_link(ev),
                related_id=ev.id,
                dedupe_exact_related=True,
            )
            if n:
                created += 1
    return created
