"""Kabupaten/Kota Indonesia (514) — sumber: Kemendagri via api-wilayah-indonesia-2026 + koordinat."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_DATA_PATH = Path(__file__).resolve().parent / "data" / "indonesia_locations.json"

_LEGACY_SLUG_TO_ID = {
    "jakarta-selatan": "3171",
    "jakarta-pusat": "3173",
    "jakarta-barat": "3174",
    "jakarta-timur": "3172",
    "jakarta-utara": "3175",
    "bandung": "3273",
    "surabaya": "3578",
    "yogyakarta": "3471",
    "bali": "5171",
    "depok": "3276",
    "tangerang": "3671",
    "bekasi": "3275",
}


@lru_cache(maxsize=1)
def _rows() -> tuple[dict, ...]:
    with _DATA_PATH.open(encoding="utf-8") as f:
        return tuple(json.load(f))


@lru_cache(maxsize=1)
def _by_id() -> dict[str, dict]:
    return {r["id"]: r for r in _rows()}


@lru_cache(maxsize=1)
def _by_slug() -> dict[str, dict]:
    return {r["slug"]: r for r in _rows()}


@lru_cache(maxsize=1)
def _by_label_lower() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for r in _rows():
        out[r["label"].lower()] = r
        out[r["label"].replace("Kab. ", "").lower()] = r
    return out


def all_locations() -> list[dict]:
    return list(_rows())


def resolve_location(key: str | None) -> dict | None:
    """Resolve Kemendagri id, legacy slug, or label to a location row."""
    if not key or not str(key).strip():
        return None
    raw = str(key).strip()
    legacy_id = _LEGACY_SLUG_TO_ID.get(raw.lower())
    if legacy_id:
        raw = legacy_id
    hit = _by_id().get(raw)
    if hit:
        return hit
    hit = _by_slug().get(raw.lower())
    if hit:
        return hit
    return _by_label_lower().get(raw.lower())


def location_label(key: str | None) -> str:
    row = resolve_location(key)
    return row["label"] if row else (key or "")


def location_coords(key: str | None) -> tuple[float, float] | None:
    row = resolve_location(key)
    if not row:
        return None
    lat, lng = row.get("latitude"), row.get("longitude")
    if lat is None or lng is None:
        return None
    return float(lat), float(lng)


def search_locations(*, q: str = "", limit: int = 50) -> list[dict]:
    query = (q or "").strip().lower()
    rows = _rows()
    if not query:
        return list(rows[:limit])
    out = []
    for r in rows:
        hay = f"{r['label']} {r['province']} {r['id']} {r['slug']}".lower()
        if query in hay:
            out.append(r)
            if len(out) >= limit:
                break
    return out
