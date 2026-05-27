"""
Rencana respons chat: intent + sumber card dari teks pertanyaan.
Mencakup prompt UI (sidebar, chip welcome, follow-up) dan pola umum bahasa Indonesia.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChatQueryPlan:
    intent: str
    fetch_events: bool = False
    fetch_communities: bool = False
    fetch_areas: bool = False
    prefer_nearby: bool = False
    prefer_weekend: bool = False


_GREETINGS = ("halo", "hai", "hey", "helo", "hi", "hello", "selamat pagi", "selamat siang", "selamat malam")
_ACK_HINTS = (
    "oke",
    "ok",
    "sip",
    "siap",
    "mantap",
    "noted",
    "siapp",
    "okay",
)

_FAQ_HINTS = (
    "apa itu ngumpulyuk",
    "ngumpsky",
    "cara daftar",
    "cara registrasi",
    "cara login",
    "cara masuk",
    "cara bikin event",
    "cara buat event",
    "cara edit event",
    "bikin event sendiri",
    "buat event sendiri",
    "cara join",
    "cara ikut",
    "cara gabung",
    "keluar event",
    "keluar komunitas",
    "lupa sandi",
    "lupa password",
    "reset password",
    "verifikasi email",
    "onboarding",
    "edit profil",
    "tab explore",
    "tab peta",
    "notifikasi",
    "privasi",
    "keamanan data",
    "ngumpulyuk itu",
    "platform ini",
    "web apa",
    "aplikasi apa",
    "kamu siapa",
    "bantuan",
    "butuh bantuan",
    "cara spill",
    "buat komunitas",
    "bikin komunitas",
)

_COMMUNITY_HINTS = (
    "komunitas",
    "community",
    "grup",
    "ngumpul bareng",
    "join komunitas",
    "gabung komunitas",
)

_EVENT_HINTS = (
    "event",
    "acara",
    "kegiatan",
    "agenda",
    "hangout",
    "kumpul",
    "rekomendasi event",
    "rekomendasi acara",
    "cari event",
    "cari acara",
    "worth it",
    "seru buat",
)

_PLACE_HINTS = (
    "deket",
    "dekat",
    "sekitar",
    "terdekat",
    "lokasiku",
    "lokasi ku",
    "dekat aku",
    "deket aku",
    "dekat sini",
    "area",
    "lokasi",
    "dimana",
    "di mana",
    "venue",
    "kota",
    "maps",
    "peta",
)

_SPORTS_HINTS = (
    "olahraga",
    "sport",
    "futsal",
    "badminton",
    "basket",
    "voli",
    "bola",
    "lari",
    "gym",
    "padel",
    "tenis",
    "workout",
    "yoga",
)

_WEEKEND_HINTS = ("weekend", "sabtu", "minggu", "libur", "week end")

_THEME_HINTS = (
    "kreatif",
    "creative",
    "temanya",
    "tema",
    "vibe",
    "seni",
    "workshop",
    "lukis",
    "fotografi",
    "craft",
    "desain",
    "design",
    "diy",
)

_ACTIVE_HINTS = ("aktif", "rame", "ramai", "lagi rame", "yang lagi")

# Prompt persis / hampir persis dari UI produk
_UI_PROMPT_PLANS: tuple[tuple[str, ChatQueryPlan], ...] = (
    (
        "ada event olahraga minggu ini yang worth it",
        ChatQueryPlan("event_reco", fetch_events=True, prefer_weekend=False),
    ),
    (
        "event seru buat weekend ini",
        ChatQueryPlan("event_reco", fetch_events=True, prefer_weekend=True),
    ),
    (
        "komunitas apa yang cocok buat aku join",
        ChatQueryPlan("community_reco", fetch_communities=True),
    ),
    (
        "komunitas yang aktif",
        ChatQueryPlan("community_reco", fetch_communities=True),
    ),
    (
        "komunitas yang lagi aktif",
        ChatQueryPlan("community_reco", fetch_communities=True),
    ),
    (
        "ada yang temanya kreatif",
        ChatQueryPlan("event_reco", fetch_events=True, fetch_communities=True),
    ),
    (
        "ada yang deket aku",
        ChatQueryPlan("place_reco", fetch_events=True, fetch_areas=True, prefer_nearby=True),
    ),
    (
        "olahraga minggu ini",
        ChatQueryPlan("event_reco", fetch_events=True),
    ),
    (
        "event weekend dong",
        ChatQueryPlan("event_reco", fetch_events=True, prefer_weekend=True),
    ),
    (
        "rekomendasi event untukku",
        ChatQueryPlan("event_reco", fetch_events=True),
    ),
    (
        "event deket lokasiku",
        ChatQueryPlan("place_reco", fetch_events=True, fetch_areas=True, prefer_nearby=True),
    ),
    (
        "event minggu ini",
        ChatQueryPlan("event_reco", fetch_events=True),
    ),
    (
        "cara daftar gimana",
        ChatQueryPlan("faq", fetch_events=False, fetch_communities=False),
    ),
    (
        "cara bikin event sendiri",
        ChatQueryPlan("faq", fetch_events=False, fetch_communities=False),
    ),
)


def _normalize(text: str) -> str:
    return " ".join((text or "").lower().strip().split())


def _is_greeting(m: str) -> bool:
    import re

    tokens = [t for t in re.split(r"[\s,.!?]+", m) if t]
    first = tokens[0] if tokens else ""
    if first not in _GREETINGS or len(m) >= 80:
        return False
    return not any(
        k in m
        for k in _COMMUNITY_HINTS + _EVENT_HINTS + _PLACE_HINTS + ("rekomendasi", "cara", "faq", "bantuan")
    )


def plan_chat_query(message_lower: str) -> ChatQueryPlan:
    m = _normalize(message_lower)
    if not m:
        return ChatQueryPlan("empty")

    for needle, plan in _UI_PROMPT_PLANS:
        if needle in m:
            return plan

    if _is_greeting(m):
        return ChatQueryPlan("greeting")

    if m in _ACK_HINTS:
        return ChatQueryPlan("ack")

    if any(h in m for h in _FAQ_HINTS):
        return ChatQueryPlan("faq")

    if any(h in m for h in _PLACE_HINTS):
        return ChatQueryPlan(
            "place_reco",
            fetch_events=True,
            fetch_areas=True,
            prefer_nearby=any(k in m for k in ("deket", "dekat", "lokasiku", "lokasi ku", "dekat aku", "deket aku")),
        )

    if any(h in m for h in _COMMUNITY_HINTS) or (
        "ada yang" in m and any(h in m for h in _ACTIVE_HINTS + _THEME_HINTS)
    ):
        fetch_both = any(h in m for h in _THEME_HINTS)
        return ChatQueryPlan(
            "community_reco" if "komunitas" in m or "grup" in m else "event_reco",
            fetch_events=fetch_both,
            fetch_communities=True,
        )

    if (
        any(h in m for h in _SPORTS_HINTS + _WEEKEND_HINTS + _THEME_HINTS)
        or "rekomendasi" in m
        or "ada yang" in m
        or any(h in m for h in _EVENT_HINTS)
    ):
        return ChatQueryPlan(
            "event_reco",
            fetch_events=True,
            fetch_communities=any(h in m for h in _THEME_HINTS),
            prefer_weekend=any(h in m for h in _WEEKEND_HINTS),
        )

    if any(h in m for h in ("cocok", "seru", "recommended", "worth", "apa aja", "apa saja")):
        return ChatQueryPlan("event_reco", fetch_events=True, fetch_communities=True)

    return ChatQueryPlan("general", fetch_events=True, fetch_communities=True)
