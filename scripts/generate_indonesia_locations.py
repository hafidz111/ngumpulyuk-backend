#!/usr/bin/env python3
"""Regenerate indonesia_locations.json from Kemendagri 2026 + koordinat."""

from __future__ import annotations

import json
import re
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_FRONTEND = (
    ROOT.parent / "ngumpulyuk-frontend" / "src" / "shared" / "data" / "indonesia-locations.json"
)
OUT_BACKEND = ROOT / "ngumpulyuk_app" / "common" / "data" / "indonesia_locations.json"

PROVINCES_URL = "https://cdn.jsdelivr.net/gh/izzulabadi/api-wilayah-indonesia-2026@v1.0.4/api/provinces.json"
REGENCIES_URL = "https://cdn.jsdelivr.net/gh/izzulabadi/api-wilayah-indonesia-2026@v1.0.4/api/regencies.json"
COORDS_URL = (
    "https://raw.githubusercontent.com/yusufsyaifudin/wilayah-indonesia/master/data/list_of_area/regencies.json"
)


def fetch(url: str) -> list | dict:
    with urllib.request.urlopen(url, timeout=60) as resp:
        return json.load(resp)


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")


def format_label(name: str) -> str:
    parts = name.strip().split()
    if not parts:
        return name
    kind = parts[0].upper()
    rest = parts[1:]
    if kind == "KOTA" and rest:
        return " ".join(w.capitalize() for w in rest)
    if kind == "KABUPATEN" and rest:
        return "Kab. " + " ".join(w.capitalize() for w in rest)
    return name.title()


def main() -> None:
    provinces = {p["id"]: p["name"] for p in fetch(PROVINCES_URL)}
    regencies = fetch(REGENCIES_URL)
    coords = {r["id"]: r for r in fetch(COORDS_URL)}

    by_prov_coords: dict[str, list[tuple[float, float]]] = {}
    out = []
    for r in regencies:
        rid = r["id"]
        pid = r["provinceId"]
        c = coords.get(rid, {})
        label = format_label(r["name"].upper())
        lat, lng = c.get("latitude"), c.get("longitude")
        if lat is not None and lng is not None:
            by_prov_coords.setdefault(pid, []).append((float(lat), float(lng)))
        out.append(
            {
                "id": rid,
                "slug": slugify(label),
                "label": label,
                "provinceId": pid,
                "province": provinces.get(pid, ""),
                "latitude": lat,
                "longitude": lng,
            }
        )

    for row in out:
        if row["latitude"] is None:
            peers = by_prov_coords.get(row["provinceId"], [])
            if peers:
                row["latitude"], row["longitude"] = peers[0]
            else:
                row["latitude"], row["longitude"] = -2.5, 118.0

    out.sort(key=lambda x: (x["province"], x["label"]))

    payload = json.dumps(out, ensure_ascii=False, separators=(",", ":"))
    OUT_FRONTEND.parent.mkdir(parents=True, exist_ok=True)
    OUT_BACKEND.parent.mkdir(parents=True, exist_ok=True)
    OUT_FRONTEND.write_text(payload, encoding="utf-8")
    OUT_BACKEND.write_text(payload, encoding="utf-8")
    print(f"Wrote {len(out)} locations to {OUT_FRONTEND} and {OUT_BACKEND}")


if __name__ == "__main__":
    main()
