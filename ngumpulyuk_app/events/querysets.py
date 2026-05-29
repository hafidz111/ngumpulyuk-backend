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


def filter_scheduled_past(qs, *, today=None):
    """Event yang tanggalnya sudah lewat (termasuk status upcoming yang belum di-update)."""
    return qs.filter(event_has_passed_q(today=today))


def filter_event_search(qs, search: str):
    """Cari di judul, deskripsi, kategori, lokasi, dan tag."""
    term = (search or "").strip()
    if not term:
        return qs
    return qs.filter(
        Q(title__icontains=term)
        | Q(description__icontains=term)
        | Q(category__icontains=term)
        | Q(location_area__icontains=term)
        | Q(location_address__icontains=term)
        | Q(tags__tag_name__icontains=term)
    ).distinct()


def event_has_passed(ev, *, today=None) -> bool:
    """True jika tanggal event sudah lewat (abaikan status DB yang belum di-update)."""
    today = today or timezone.localdate()
    if ev.end_date is not None:
        return ev.end_date < today
    return ev.event_date < today
