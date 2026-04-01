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
    return {
        "id": str(u.id),
        "username": u.username,
        "full_name": u.full_name,
        "profile_picture": u.profile_picture,
    }


def mini_user_creator(u):
    return {
        "id": str(u.id),
        "username": u.username,
    }
