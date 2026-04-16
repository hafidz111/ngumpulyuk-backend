"""
Interest taxonomy helpers.

Source of truth:
- existing stored user interests in database (normalized slug values)
"""
from __future__ import annotations

from django.db.models import Count

from ngumpulyuk_app.users.models import UserInterest


def normalize_interest(value: str) -> str:
    return (value or "").strip().lower()


def get_interest_taxonomy() -> list[str]:
    return sorted(
        {
            normalize_interest(v)
            for v in UserInterest.objects.values_list("interest_name", flat=True).distinct()
            if normalize_interest(v)
        }
    )


def get_interest_popularity() -> list[dict]:
    """
    Return interest popularity ordered by user count (desc), then interest (asc).
    Count reflects number of distinct users per normalized interest.
    """
    raw_rows = (
        UserInterest.objects.values("interest_name")
        .annotate(user_count=Count("user_id", distinct=True))
        .order_by()
    )
    merged: dict[str, int] = {}
    for row in raw_rows:
        key = normalize_interest(row["interest_name"])
        if not key:
            continue
        merged[key] = merged.get(key, 0) + int(row["user_count"])

    ranked = sorted(merged.items(), key=lambda x: (-x[1], x[0]))
    return [{"interest": interest, "count": count} for interest, count in ranked]
