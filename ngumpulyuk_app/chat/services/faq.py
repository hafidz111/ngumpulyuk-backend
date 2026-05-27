"""
FAQ statis untuk Ngumpsky (chat assistant).
Jawaban user-facing: tanpa istilah teknis (database, API, dll).
"""

from __future__ import annotations

FAQ_ENTRIES = [
    {
        "id": "how-to-join-generic",
        "keywords": ("cara bergabung", "bagaimana cara bergabung", "gimana gabung", "cara join"),
        "aliases": (
            "bagaimana cara bergabung",
            "cara bergabung",
            "gimana cara bergabung",
            "cara join gimana",
        ),
        "title": "Cara bergabung",
        "answer": (
            "Kalau mau gabung event, buka detail event lalu tap Join. "
            "Kalau mau gabung komunitas (circle), buka detail circle lalu tap Gabung. "
            "Kalau bingung pilih yang mana, bilang aja: event atau komunitas, nanti gue arahin step-by-step."
        ),
    },
    {
        "id": "what-is",
        "keywords": ("apa itu", "ngumpulyuk", "platform", "buat apa", "fungsi app"),
        "aliases": (
            "web apa ini",
            "ini web apa",
            "ini aplikasi apa",
            "aplikasi apa ini",
            "platform apa ini",
            "ini platform apa",
            "website apa ini",
            "ngumpulyuk itu apa",
        ),
        "title": "NgumpulYuk itu apa?",
        "answer": (
            "NgumpulYuk itu tempat buat cari event dan komunitas (circle), ikutan kegiatan, "
            "dan ngobrol sama orang yang vibes-nya mirip. Fokusnya ngumpul di dunia nyata, "
            "bukan cuma scroll feed."
        ),
    },
    {
        "id": "ngumpsky",
        "keywords": ("ngumpsky", "asisten", "chat bot", "bestie", "siapa kamu"),
        "aliases": (
            "kamu siapa",
            "lu siapa",
            "ini siapa",
            "bisa tanya apa",
            "ngumpsky itu apa",
        ),
        "title": "Ngumpsky (asisten chat)",
        "answer": (
            "Ngumpsky itu bestie digital di tab Chat. Kamu bisa tanya rekomendasi event, "
            "komunitas, atau area yang lagi rame. Kalau ada datanya, Ngumpsky kasih card biar "
            "langsung bisa dibuka. Kalau belum ada yang cocok, coba Explore atau update minat di profil."
        ),
    },
    {
        "id": "account-register",
        "keywords": ("daftar", "registrasi", "register", "sign up", "buat akun"),
        "aliases": (
            "cara daftar gimana",
            "gimana daftar",
            "how to register",
            "mau daftar",
        ),
        "title": "Cara daftar akun",
        "answer": (
            "Buka halaman Daftar, isi email, nama, dan password, lalu selesaikan verifikasi email "
            "kalau diminta. Setelah login, biasanya ada onboarding singkat buat isi minat dan preferensi."
        ),
    },
    {
        "id": "account-login",
        "keywords": ("login", "masuk", "sign in", "log in"),
        "aliases": (
            "cara login",
            "gimana login",
            "gimana masuk",
        ),
        "title": "Cara login",
        "answer": (
            "Pakai email dan password yang udah didaftarin di layar Masuk. "
            "Kalau ada opsi login Google di versi app kamu, itu juga bisa dipakai."
        ),
    },
    {
        "id": "account-password",
        "keywords": ("lupa password", "lupa sandi", "reset password", "ganti password"),
        "aliases": (
            "password lupa",
            "sandi lupa",
            "forgot password",
        ),
        "title": "Lupa password",
        "answer": (
            "Di layar login, pilih Lupa password, masukin email terdaftar, terus ikuti link reset "
            "yang dikirim ke email kamu. Kalau email gak masuk, cek folder spam dulu."
        ),
    },
    {
        "id": "account-verify",
        "keywords": ("verifikasi email", "verify email", "aktivasi email", "konfirmasi email"),
        "aliases": (
            "email belum verifikasi",
            "link verifikasi",
        ),
        "title": "Verifikasi email",
        "answer": (
            "Setelah daftar, buka email verifikasi dari NgumpulYuk dan klik link-nya. "
            "Tanpa verifikasi, beberapa fitur mungkin belum bisa dipakai penuh."
        ),
    },
    {
        "id": "onboarding",
        "keywords": ("onboarding", "minat", "preferensi", "pertama kali", "setup profil"),
        "aliases": (
            "isi minat",
            "atur minat",
            "profil awal",
        ),
        "title": "Onboarding & minat",
        "answer": (
            "Pas pertama masuk, kamu isi minat aktivitas, area, dan waktu favorit. "
            "Ini bantu rekomendasi event dan jawaban Ngumpsky yang lebih nyambung sama kamu. "
            "Bisa diubah lagi lewat Profil."
        ),
    },
    {
        "id": "profile",
        "keywords": ("profil", "edit profil", "ubah profil", "foto profil", "bio"),
        "aliases": (
            "gimana edit profil",
            "update profil",
        ),
        "title": "Profil kamu",
        "answer": (
            "Buka tab Profil buat lihat dan edit info kamu: nama, minat, preferensi lokasi, "
            "event yang diikuti, dan komunitas yang udah dijoin. Profil rapi = rekomendasi lebih pas."
        ),
    },
    {
        "id": "explore-events",
        "keywords": ("explore", "jelajah", "cari event", "lihat event", "daftar event"),
        "aliases": (
            "tab explore",
            "halaman event",
            "event apa aja",
        ),
        "title": "Explore event",
        "answer": (
            "Tab Explore nunjukin event yang mau datang dan yang udah lewat. "
            "Kamu bisa search, filter, terus buka detail buat join. Mau ngadain sendiri? "
            "Tap Buat Event."
        ),
    },
    {
        "id": "join-event",
        "keywords": ("join event", "ikut event", "gabung event", "daftar event", "slot event"),
        "aliases": (
            "cara join",
            "cara ikut event",
            "gimana join event",
            "masih ada slot",
        ),
        "title": "Ikut event",
        "answer": (
            "Buka detail event, cek tanggal, lokasi, dan kuota peserta. "
            "Kalau masih ada slot dan belum lewat batas daftar, tap join. "
            "Event yang udah kamu ikuti muncul di Profil."
        ),
    },
    {
        "id": "leave-event",
        "keywords": ("keluar event", "cancel join", "batal ikut", "unjoin", "leave event"),
        "aliases": (
            "gimana keluar event",
            "batal join",
        ),
        "title": "Keluar dari event",
        "answer": (
            "Di detail event yang udah kamu join, ada opsi keluar atau batalkan partisipasi "
            "(kalau masih disediakan di versi app). Slot kamu bakal lepas buat peserta lain."
        ),
    },
    {
        "id": "create-event",
        "keywords": ("bikin event", "buat event", "create event", "ngadain event", "jadwal sendiri"),
        "aliases": (
            "cara bikin event sendiri",
            "gimana bikin event",
            "buat event gimana",
            "mau bikin event",
        ),
        "title": "Bikin event sendiri",
        "answer": (
            "Dari tab Chat atau Explore, tap Buat Event. Isi judul, kategori, tanggal mulai dan selesai, "
            "lokasi di peta, kuota peserta, dan deskripsi. Setelah publish, orang lain bisa join lewat detail event."
        ),
    },
    {
        "id": "edit-event",
        "keywords": ("edit event", "ubah event", "update event", "ganti jadwal event"),
        "aliases": (
            "cara edit event",
        ),
        "title": "Edit event",
        "answer": (
            "Kalau kamu pembuat event, buka detail event lalu pilih edit (biasanya dari menu pengaturan event). "
            "Update info penting kayak tanggal, lokasi, atau kuota kalau ada perubahan."
        ),
    },
    {
        "id": "map-events",
        "keywords": ("peta", "map", "lokasi event", "event deket", "event terdekat"),
        "aliases": (
            "tab peta",
            "buka peta",
            "cari di peta",
        ),
        "title": "Peta event",
        "answer": (
            "Tab Peta nunjukin event yang belum lewat biar gampang lihat yang deket lokasi kamu. "
            "Kamu bisa search nama event di peta, terus buka detail dari pin-nya."
        ),
    },
    {
        "id": "recommendations",
        "keywords": ("rekomendasi", "recommended", "cocok buatku", "saran event", "personalized"),
        "aliases": (
            "event untukku",
            "yang cocok sama aku",
        ),
        "title": "Rekomendasi event",
        "answer": (
            "Rekomendasi ngikutin minat, aktivitas, dan lokasi yang kamu isi di profil. "
            "Muncul di welcome Chat dan saat kamu tanya Ngumpsky. "
            "Kalau kurang pas, update minat di Profil atau explore manual di tab Explore."
        ),
    },
    {
        "id": "communities-intro",
        "keywords": ("komunitas", "circle", "apa itu komunitas", "bedanya komunitas"),
        "aliases": (
            "community apa",
            "grup ngumpul",
        ),
        "title": "Komunitas (circle)",
        "answer": (
            "Komunitas itu circle buat diskusi dan spill update seputar satu minat. "
            "Ada feed obrolan umum dan circle yang bisa kamu join. "
            "Di dalam circle kamu bisa spill thread dan link event yang kamu ikuti."
        ),
    },
    {
        "id": "join-community",
        "keywords": ("gabung komunitas", "join komunitas", "join circle", "masuk komunitas"),
        "aliases": (
            "cara gabung circle",
            "gimana join komunitas",
            "cara gabung komunitas bagaimana",
            "cara gabung komunitas",
        ),
        "title": "Gabung komunitas",
        "answer": (
            "Buka detail circle yang kamu mau, lalu tap Gabung. "
            "Setelah join, kamu bisa spill thread di circle itu dan lihat member lain."
        ),
    },
    {
        "id": "see-members",
        "keywords": ("lihat member", "member lain", "anggota komunitas", "daftar member"),
        "aliases": (
            "bagaimana cara lihat member lain",
            "cara lihat member lain",
            "lihat member komunitas",
            "cek anggota komunitas",
        ),
        "title": "Lihat member komunitas",
        "answer": (
            "Masuk ke halaman detail circle, lalu scroll ke bagian Member/Anggota. "
            "Di situ kamu bisa lihat siapa aja yang join komunitas itu."
        ),
    },
    {
        "id": "leave-community",
        "keywords": ("keluar komunitas", "leave community", "unjoin komunitas"),
        "aliases": (
            "cara keluar circle",
            "gimana keluar komunitas",
        ),
        "title": "Keluar dari komunitas",
        "answer": (
            "Di halaman detail komunitas yang udah kamu join, tap Keluar. "
            "Kamu gak akan lihat thread circle itu di daftar circle kamu lagi."
        ),
    },
    {
        "id": "community-thread",
        "keywords": ("spill", "thread", "obrolan", "post komunitas", "komentar komunitas"),
        "aliases": (
            "cara spill",
            "buat thread",
            "posting di circle",
        ),
        "title": "Spill & thread",
        "answer": (
            "Di tab Komunitas, bagian Obrolan atau di detail circle, ketik spill di composer. "
            "Kamu bisa pilih circle, upload foto, atau link event yang lagi kamu ikuti. "
            "Thread bisa dibuka buat baca komentar dan ikut diskusi."
        ),
    },
    {
        "id": "create-community",
        "keywords": ("bikin komunitas", "buat komunitas", "buat circle", "create community"),
        "aliases": (
            "cara buat komunitas",
            "gimana bikin circle",
        ),
        "title": "Bikin komunitas sendiri",
        "answer": (
            "Dari halaman Komunitas, tap Buat Komunitas. Isi nama, deskripsi, kategori, "
            "dan cover (opsional). Kamu jadi admin circle dan bisa kelola member."
        ),
    },
    {
        "id": "notifications",
        "keywords": ("notifikasi", "notification", "push", "bell", "pemberitahuan"),
        "aliases": (
            "cara lihat notifikasi",
            "notif",
        ),
        "title": "Notifikasi",
        "answer": (
            "Buka halaman Notifikasi buat lihat update event, komunitas, dan info penting lain. "
            "Tap notifikasi buat tandai dibaca. Beberapa update juga bisa lewat push di perangkat kamu "
            "kalau izin notifikasi aktif."
        ),
    },
    {
        "id": "privacy",
        "keywords": ("privasi", "data pribadi", "keamanan", "aman tidak", "aman gak"),
        "aliases": (
            "data aman",
            "keamanan data",
        ),
        "title": "Privasi & keamanan",
        "answer": (
            "Jangan share nomor HP, alamat rumah, atau password di chat Ngumpsky. "
            "Untuk masalah akun sensitif, hubungi kanal support resmi NgumpulYuk. "
            "Ngumpsky cuma bantu info event dan komunitas di dalam app."
        ),
    },
    {
        "id": "no-match-help",
        "keywords": ("gak ada", "tidak ada", "kosong", "belum ada", "gak ketemu"),
        "aliases": (
            "ga ada event",
            "kok kosong",
        ),
        "title": "Belum nemu yang cocok?",
        "answer": (
            "Coba tab Explore buat cari manual, buka Peta buat yang deket, atau update minat di Profil. "
            "Di Chat, tanya lebih spesifik kayak olahraga minggu ini, weekend, atau komunitas yang aktif."
        ),
    },
    {
        "id": "support",
        "keywords": ("bantuan", "help", "support", "hubungi", "kontak", "lapor"),
        "aliases": (
            "butuh bantuan",
            "ada masalah",
        ),
        "title": "Butuh bantuan?",
        "answer": (
            "Untuk bug atau masalah akun, hubungi tim NgumpulYuk lewat kanal support resmi. "
            "Sertakan screenshot dan langkah yang kamu lakukan biar cepat ditangani."
        ),
    },
]


CANONICAL_ALIASES = {e["id"]: tuple(e.get("aliases") or ()) for e in FAQ_ENTRIES if e.get("aliases")}


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
                "aliases": list(e.get("aliases") or ()),
            }
        )
    return items


def _score_entry(message_lower: str, entry: dict) -> int:
    score = 0
    for keyword in entry.get("keywords") or ():
        if keyword in message_lower:
            score += max(len(keyword), 3)
    for alias in entry.get("aliases") or ():
        if alias in message_lower:
            score += len(alias) + 10
    return score


def match_faq(message_lower: str, limit: int = 3):
    m = (message_lower or "").strip()
    if not m:
        return []

    alias_hits: list[tuple[int, dict]] = []
    for entry in FAQ_ENTRIES:
        for alias in entry.get("aliases") or ():
            if alias in m:
                alias_hits.append((len(alias), entry))
    if alias_hits:
        alias_hits.sort(key=lambda x: (-x[0], x[1]["id"]))
        seen: set[str] = set()
        out: list[dict] = []
        for _, entry in alias_hits:
            if entry["id"] in seen:
                continue
            seen.add(entry["id"])
            out.append(entry)
            if len(out) >= limit:
                return out

    scored: list[tuple[int, dict]] = []
    for entry in FAQ_ENTRIES:
        score = _score_entry(m, entry)
        if score:
            scored.append((score, entry))
    scored.sort(key=lambda x: (-x[0], x[1]["id"]))
    return [e for _, e in scored[:limit]]
