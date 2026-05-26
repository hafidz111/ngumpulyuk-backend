"""Constants for synthetic seed data (Indonesian locale)."""

SYNTHETIC_EMAIL_DOMAIN = "seed.ngumpulyuk.local"
SYNTHETIC_PASSWORD = "SynSeed2026!"

REFERENCE_TODAY = "2026-05-26"
EVENT_DATE_MIN = "2026-04-07"

FIRST_NAMES_MALE = [
    "Aldi", "Budi", "Dimas", "Eko", "Fajar", "Hendra", "Irfan", "Joko", "Kevin", "Lukman",
    "Nanda", "Omar", "Putra", "Rizky", "Satria", "Teguh", "Umar", "Wahyu", "Yoga", "Zaki",
    "Agus", "Bayu", "Candra", "Doni", "Gilang", "Edo", "Indra", "Jaya", "Krisna", "Lutfi",
]

FIRST_NAMES_FEMALE = [
    "Ayu", "Bella", "Citra", "Dewi", "Eka", "Fitri", "Gita", "Hana", "Intan", "Jessica",
    "Kartika", "Lia", "Maya", "Nadia", "Olivia", "Putri", "Rina", "Sari", "Tika", "Ulya",
    "Vina", "Wulan", "Yuni", "Zahra", "Amelia", "Bunga", "Clara", "Dinda", "Elsa", "Farah",
]

LAST_NAMES = [
    "Pratama", "Wijaya", "Santoso", "Saputra", "Hidayat", "Kusuma", "Ramadhan", "Nugroho",
    "Setiawan", "Permana", "Utami", "Lestari", "Anggraini", "Mahardika", "Purnomo", "Siregar",
    "Halim", "Gunawan", "Firmansyah", "Iskandar", "Maulana", "Syahputra", "Wibowo", "Susanto",
]

# Kabupaten/Kota (514) — data lengkap di common/data/indonesia_locations.json
from ngumpulyuk_app.common.indonesia_locations import all_locations

LOCATIONS = [r["label"] for r in all_locations()]

LOCATION_GEO = {
    r["label"]: (float(r["latitude"]), float(r["longitude"]))
    for r in all_locations()
    if r.get("latitude") is not None and r.get("longitude") is not None
}

STREET_NAMES = [
    "Sudirman", "Thamrin", "Kemang", "Fatmawati", "Gatot Subroto",
    "Dago", "Asia Afrika", "Pahlawan", "Ahmad Yani", "Merdeka",
]

INTERESTS = [
    "running", "padel", "cycling", "yoga", "basketball", "pokemon", "boardgames",
    "hiking", "swimming", "badminton", "photography", "cooking", "futsal", "tennis",
    "workshop", "networking", "gaming", "music", "art", "tech",
]

EVENT_CATEGORIES = [
    "Olahraga", "Futsal", "Running", "Workshop", "Seni", "Gaming", "Social", "Networking",
    "Kelas", "Meetup", "Yoga", "Cycling", "Basketball", "Teknologi", "Kuliner",
]

COMMUNITY_CATEGORIES = [
    "Olahraga", "Gaming", "Seni", "Kreatif", "Teknologi", "Social", "Kuliner", "Outdoor",
    "Futsal", "Running", "Networking", "Hobi",
]

PREFERRED_DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
PREFERRED_TIMES = ["morning", "afternoon", "evening", "night"]

EVENT_TITLES = [
    "Ngumpul {cat} {area}",
    "Sesi {cat} Bareng",
    "Meetup {cat} Akhir Pekan",
    "Workshop {cat} Santai",
    "Turnamen {cat} Komunitas",
    "Latihan {cat} Open",
    "Hangout {cat} Senja",
    "Circle {cat} Mingguan",
]

COMMUNITY_NAMES = [
    "Komunitas {cat} {area}",
    "Circle {cat} {area}",
    "Ngumpul {cat} ID",
    "Squad {cat} {area}",
    "{cat} Enthusiasts {area}",
]

GLOBAL_THREAD_COUNT = 200

GLOBAL_THREAD_TITLES = [
    "Weekend ini ada event seru?",
    "Cari temen {topic} di {area}",
    "Spill event kemarin dong",
    "Komunitas apa yang lagi rame?",
    "Baru join, kenalan yuk",
    "Lapangan futsal murah di {area}?",
    "Event gratis yang worth it?",
    "Sabtu pagi ada rencana ngumpul?",
    "Yang pernah ke PIK jogging, gimana?",
    "Rekomendasi meetup malam di {area}",
]

GLOBAL_THREAD_BODIES = [
    "Lagi nyari aktivitas {topic} yang santai, zona {area}. Kalau ada info event atau circle, drop di sini.",
    "Kemarin ikut acara seru, cuma parkirnya agak jauh. Ada alternatif lokasi yang lebih deket?",
    "Baru pindah ke {area}, belum banyak kenalan. Enaknya mulai dari event apa ya?",
    "Pengen rutin ngumpul tiap minggu, tapi jadwal kerja agak berantakan. Ada tips atur waktunya?",
    "Siapa tau ada slot kosong buat main {topic}? Bisa join dari jam sore.",
    "Capek kerja remote, pengen keluar bentar. Event outdoor atau indoor enaknya yang mana?",
    "Ada yang sama-sama suka {topic}? Bisa bikin grup kecil dulu.",
    "Kemarin cuacanya mendung, tapi tetap jadi. Next kali kapan ya ada jadwal lagi?",
]

THREAD_TITLES = [
    "Ada yang ikut event minggu depan?",
    "Rekomendasi lapangan di {area}",
    "Spill event kemarin dong",
    "Cari temen bareng {topic}",
    "Tips biar nggak telat ke lokasi",
    "Review lokasi kemarin, worth it nggak?",
    "Jadwal ngumpul favorit kalian kapan?",
    "Member baru, perkenalan dulu yuk",
]

COMMUNITY_THREAD_BODIES = [
    "Info terbaru buat yang mau ikut minggu depan. Kuota masih ada nggak ya?",
    "Biasanya kumpul di {area} jam berapa biar nggak macet?",
    "Kemarin rame banget, next batch kapan?",
    "Ada yang bisa share tips persiapan sebelum main {topic}?",
    "Lokasi kemarin parkirnya lumayan lega, recommended.",
    "Yang baru gabung jangan sungkan nanya, kita bantu.",
]

EVENT_DESCRIPTIONS = [
    "Ngumpul santai, boleh bawa teman. Datang 15 menit lebih awal buat perkenalan.",
    "Sesi ini untuk semua level. Coach singkat di awal, lalu main bareng.",
    "Bawa air minum dan handuk kecil. Parkir tersedia di area venue.",
    "Setelah main, ngopi sebentar (opsional). Konfirmasi kehadiran biar slot aman.",
    "Dress code santai. Kalau hujan, kita pindah ke indoor (info menyusul di grup).",
]

COMMUNITY_DESCRIPTIONS = [
    "Circle ini rutin ngumpul di {area}. Fokus {cat}, vibes santai, no gatekeeping.",
    "Tempat sharing jadwal, tips, dan rekomendasi lapangan. Member baru selalu welcome.",
    "Kita sering adain sesi bareng tiap pekan. Join kalau lagi cari temen sehobby.",
]

COMMENT_SNIPPETS = [
    "Setuju, makasih infonya!",
    "Aku juga mau ikut, kabarin kalau ada slot.",
    "Kemarin seru, next time ajak lagi.",
    "Lokasinya enak, parkirnya lumayan lega.",
    "Kayaknya cocok buat pemula juga.",
    "Sabtu pagi oke buatku.",
    "Ada yang dari {area}?",
    "Noted, nanti coba daftar.",
    "Sama, lagi nyari yang kayak gini.",
    "Count me in batch berikutnya.",
]
