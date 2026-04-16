import re


def classify_intent(message_lower: str) -> str:
    m = message_lower.strip()
    if not m:
        return "empty"

    greetings = ("halo", "hai", "hey", "helo", "hi", "hello", "selamat pagi", "selamat siang", "selamat malam")
    tokens = [t for t in re.split(r"[\s,.!?]+", m) if t]
    first = tokens[0] if tokens else ""
    if first in greetings and len(m) < 80:
        if not any(
            k in m
            for k in (
                "event",
                "komunitas",
                "rekomendasi",
                "tempat",
                "lokasi",
                "faq",
                "bantuan",
                "cara",
            )
        ):
            return "greeting"

    if any(
        w in m
        for w in (
            "rekomendasi event",
            "rekomendasi acara",
            "event apa",
            "acara apa",
            "event yang",
            "acara yang",
            "cari event",
            "cari acara",
            "kegiatan apa",
            "agenda apa",
            "mau ikut event",
            "mau ikut acara",
            "jadwal event",
            "jadwal acara",
            "event",
            "acara",
            "kegiatan",
            "agenda",
            "hangout",
            "kumpul",
        )
    ):
        return "event_reco"

    if any(w in m for w in ("komunitas", "community", "grup", "ngumpul bareng")):
        return "community_reco"

    if any(
        w in m
        for w in (
            "tempat",
            "lokasi",
            "dimana",
            "di mana",
            "venue",
            "area",
            "kota",
            "maps",
        )
    ):
        return "place_reco"

    if any(
        w in m
        for w in (
            "apa itu ngumpulyuk",
            "ngumpulyuk",
            "cara daftar",
            "cara pakai",
            "password",
            "lupa sandi",
            "verifikasi",
            "privasi",
            "keamanan",
            "faq",
            "bantuan",
            "help",
        )
    ):
        return "faq"

    return "general"
