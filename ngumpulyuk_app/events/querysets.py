from django.db.models import Q
from django.utils import timezone


def event_still_active_q(*, today=None) -> Q:
    """
    Event belum selesai: end_date >= today, atau tanpa end_date dan event_date >= today.
    """
    today = today or timezone.localdate()
    return Q(end_date__isnull=False, end_date__gte=today) | Q(
        end_date__isnull=True, event_date__gte=today
    )


def event_has_passed_q(*, today=None) -> Q:
    today = today or timezone.localdate()
    return Q(end_date__isnull=False, end_date__lt=today) | Q(
        end_date__isnull=True, event_date__lt=today
    )


def filter_scheduled_upcoming(qs, *, today=None):
    """status upcoming + tanggal masih aktif (belum lewat)."""
    return qs.filter(status="upcoming").filter(event_still_active_q(today=today))
