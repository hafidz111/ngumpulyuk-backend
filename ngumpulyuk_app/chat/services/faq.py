"""
FAQ statis (bukan generatif). Perluasan: pindah ke DB atau file CMS.
"""

FAQ_ENTRIES = [
    {
        "id": "what-is",
        "keywords": ("apa itu", "ngumpulyuk", "platform", "buat apa"),
        "title": "NgumpulYuk itu apa?",
        "answer": (
            "NgumpulYuk itu platform buat cari event & komunitas, ikutan kegiatan, "
            "dan diskusi bareng orang yang vibe-nya sama. Fokusnya ngumpul di dunia nyata, bukan cuma scroll doang."
        ),
    },
    {
        "id": "account",
        "keywords": ("daftar", "akun", "login", "masuk", "register"),
        "title": "Cara punya akun",
        "answer": (
            "Daftar lewat flow registrasi di app, atau login pakai opsi yang tersedia. "
            "Kalau lupa password, pakai fitur reset password di layar login (kalau sudah disediakan di versi app kamu)."
        ),
    },
    {
        "id": "privacy",
        "keywords": ("privasi", "data", "aman", "keamanan"),
        "title": "Privasi & data",
        "answer": (
            "Jangan share nomor/email sensitif di chat assistant. "
            "Buat bantuan akun yang butuh data pribadi, hubungi support resmi lewat kanal resmi app."
        ),
    },
    {
        "id": "events",
        "keywords": ("event", "ikut", "join", "peserta"),
        "title": "Event & partisipasi",
        "answer": (
            "Buka detail event, cek tanggal & kuota, terus join kalau masih ada slot. "
            "Rekomendasi di app bisa bantu nyari yang cocok sama minat kamu."
        ),
    },
    {
        "id": "communities",
        "keywords": ("komunitas", "member", "grup"),
        "title": "Komunitas",
        "answer": (
            "Komunitas itu space buat diskusi & info seputar minat tertentu. "
            "Gabung biar update thread dan kegiatan dari komunitas tersebut."
        ),
    },
]


CANONICAL_ALIASES = {
    "what-is": (
        "web apa ini",
        "ini web apa",
        "ini aplikasi apa",
        "aplikasi apa ini",
        "platform apa ini",
        "ini platform apa",
        "website apa ini",
    ),
}


def _by_id(fid: str):
    for e in FAQ_ENTRIES:
        if e["id"] == fid:
            return e
    return None


def get_faq_by_id(fid: str):
    return _by_id((fid or "").strip())


def list_faq_templates():
    items = []
    for e in FAQ_ENTRIES:
        items.append(
            {
                "id": e["id"],
                "title": e["title"],
                "answer": e["answer"],
                "keywords": list(e.get("keywords") or []),
                "aliases": list(CANONICAL_ALIASES.get(e["id"], ())),
            }
        )
    return items


def match_faq(message_lower: str, limit: int = 3):
    # Canonical alias mapping: different wording, same FAQ answer.
    for fid, aliases in CANONICAL_ALIASES.items():
        if any(a in message_lower for a in aliases):
            entry = _by_id(fid)
            return [entry] if entry else []

    scored = []
    for entry in FAQ_ENTRIES:
        score = sum(1 for k in entry["keywords"] if k in message_lower)
        if score:
            scored.append((score, entry))
    scored.sort(key=lambda x: (-x[0], x[1]["id"]))
    return [e for _, e in scored[:limit]]
