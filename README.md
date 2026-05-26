# NgumpulYuk — Backend API

REST API untuk **NgumpulYuk**, platform ngumpul berbasis komunitas: event, circle (komunitas), obrolan thread, peta lokasi, notifikasi, dan asisten chat **Ngumpsky** (AI).

## Deskripsi

Backend ini menyediakan autentikasi (email + Google OAuth), manajemen event & komunitas, diskusi (thread/komentar/like), rekomendasi, notifikasi, integrasi chat LLM (Gemini), serta data wilayah administrasi Indonesia (514 kabupaten/kota) untuk pemilihan lokasi event.

Arsitektur mengikuti domain Django apps (`authentication`, `events`, `communities`, `discussions`, `chat`, dll.) dengan Django REST Framework dan dokumentasi OpenAPI (Swagger/ReDoc).

## Fitur utama

| Modul | Fitur |
|--------|--------|
| **Autentikasi** | Register, login JWT, verifikasi email, reset password, Google OAuth |
| **Users** | Profil, onboarding (minat & preferensi), aktivitas |
| **Events** | CRUD event, join/leave, kategori, filter & pagination, upload cover |
| **Communities** | Circle, member, admin, join/leave |
| **Discussions** | Thread global & per circle, komentar, like |
| **Notifications** | In-app notifications, blast (staff) |
| **Chat (Ngumpsky)** | Percakapan AI, rekomendasi event/circle, monitoring & koreksi (admin) |
| **Recommendations** | Sinyal & rekomendasi event |
| **Common** | Landing public stats, daftar lokasi Indonesia, seed data sintetis |

## Teknologi

- **Python 3.9+**
- **Django 4.2** + **Django REST Framework**
- **PostgreSQL** (Supabase) via `DATABASE_URL`
- **JWT** — `djangorestframework-simplejwt`
- **API docs** — `drf-spectacular` (Swagger UI: `/docs/api/`)
- **CORS** — `django-cors-headers`
- **Email** — SMTP (Mailtrap untuk development)
- **Google OAuth** — login sosial
- **Firebase Admin** — (jika dikonfigurasi untuk notifikasi push)
- **LLM** — Google Gemini (chat Ngumpsky)

## Alur user (tingkat API)

```mermaid
flowchart LR
  A[Register / Login] --> B[Onboarding]
  B --> C[Explore Event]
  C --> D[Join Event / Buat Event]
  B --> E[Komunitas & Thread]
  E --> F[Spill / Komentar / Like]
  C --> G[Peta Event]
  B --> H[Chat Ngumpsky]
  H --> C
  H --> E
```

1. User mendaftar atau login (email / Google) → verifikasi email jika perlu.
2. Onboarding: minat, lokasi preferensi (kab/kota), waktu favorit.
3. Jelajahi event (upcoming/past), join, atau buat event sendiri (lokasi + koordinat).
4. Gabung circle, posting thread, komentar, like.
5. Tanya **Ngumpsky** di chat untuk rekomendasi event/komunitas.
6. Terima notifikasi aktivitas (join, thread, dll.).

## Prasyarat

- Python 3.9+
- PostgreSQL (disarankan Supabase dengan connection pooler port **6543**)
- Akun Mailtrap (dev email) & Google Cloud OAuth (opsional)
- API key Gemini (untuk chat)

## Menjalankan project

### 1. Clone & virtual environment

```bash
cd ngumpulyuk-backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment variables

Buat file **`.env`** di root backend (file ini **tidak** di-commit). Salin variabel berikut dan isi nilainya:

```env
SECRET_KEY=generate-a-strong-secret-key
DEBUG=True
DJANGO_ENV=development
ALLOWED_HOSTS=localhost,127.0.0.1

DATABASE_URL=postgresql://USER:PASSWORD@HOST:6543/postgres

FRONTEND_URL=http://localhost:5173

EMAIL_HOST_USER=your-mailtrap-user
EMAIL_HOST_PASSWORD=your-mailtrap-password

GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
SOCIAL_AUTH_PASSWORD=random-string-for-social-users
```

> **Catatan:** Template `.env.example` sengaja tidak ada di repository Git. Jika pernah ter-push, hapus dari remote dengan langkah di bawah.

### 3. Migrasi database

```bash
python manage.py migrate
```

### 4. (Opsional) Superuser & seed sintetis

```bash
python manage.py createsuperuser

# Data demo (user *@seed.ngumpulyuk.local)
python manage.py seed_synthetic_data --clear
```

### 5. Jalankan server

```bash
python manage.py runserver
```

API base: `http://127.0.0.1:8000/api/v1/`  
Swagger: `http://127.0.0.1:8000/docs/api/`

## Menghapus `.env.example` dari GitHub

Jika `.env.example` (atau `.env` berisi rahasia) pernah ter-push:

```bash
# Hentikan pelacakan file (tetap ada di laptop)
git rm --cached .env.example

# Pastikan .gitignore memuat .env.example
git add .gitignore
git commit -m "chore: stop tracking env example file"
git push origin main
```

File hilang dari GitHub pada commit berikutnya, tetapi **masih ada di history commit lama**.

### Membersihkan history (jika pernah commit `.env` berisi password asli)

```bash
# Ganti path jika perlu; backup repo dulu
git filter-repo --path .env.example --invert-paths
# atau BFG Repo-Cleaner untuk .env

git push origin main --force
```

Setelah force-push: **rotate semua secret** (DB password, `SECRET_KEY`, OAuth, Gemini, dll.).

## Endpoint berguna

| Path | Keterangan |
|------|------------|
| `GET /api/v1/public/landing/` | Data landing (stats, spotlight) |
| `GET /api/v1/locations/` | Kabupaten/kota Indonesia (`?search=`) |
| `GET /api/v1/events/categories/` | Kategori event |
| `POST /api/v1/auth/register/` | Registrasi |
| `POST /api/v1/chat/` | Chat Ngumpsky |

## Struktur folder (ringkas)

```
ngumpulyuk-backend/
├── manage.py
├── ngumpulyuk_project/      # settings, urls
├── ngumpulyuk_app/
│   ├── authentication/
│   ├── events/
│   ├── communities/
│   ├── discussions/
│   ├── chat/
│   ├── notifications/
│   ├── users/
│   └── common/              # landing, locations, seed
├── requirements.txt
└── scripts/
    └── generate_indonesia_locations.py
```

## Lisensi

Proyek privat — sesuaikan dengan kebijakan tim Anda.
