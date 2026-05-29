def clamp_limit(val, default=20, max_val=100):
    try:
        n = int(val)
    except (TypeError, ValueError):
        return default
    return max(1, min(n, max_val))


def clamp_offset(val, default=0):
    try:
        n = int(val)
    except (TypeError, ValueError):
        return default
    return max(0, n)


def pagination_meta(total, limit, offset):
    """Fields documented in API-documentation.md (Pagination section)."""
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total,
    }


def mini_user(u):
    if not u:
        return None
    interest_rows = getattr(u, "interest_rows", None)
    if interest_rows is not None and hasattr(interest_rows, "all"):
        interests = [row.interest_name for row in interest_rows.all()]
    else:
        interests = []
    return {
        "id": str(u.id),
        "username": u.username,
        "full_name": u.full_name,
        "profile_picture": u.profile_picture,
        "interest": interests[0] if interests else None,
        "interests": interests,
    }


def mini_user_creator(u):
    return {
        "id": str(u.id),
        "username": u.username,
    }


def mini_user_event_participant(u):
    """Ringan untuk daftar peserta event — tanpa query interest per user."""
    if not u:
        return None
    return {
        "id": str(u.id),
        "username": u.username,
        "full_name": u.full_name,
        "profile_picture": u.profile_picture,
    }
