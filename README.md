# NgumpulYuk — Backend API

REST API untuk **NgumpulYuk**, platform ngumpul berbasis komunitas: event, circle (komunitas), obrolan thread, peta lokasi, notifikasi, dan asisten chat **Ngumpsky** (AI).

## Deployment (production)

|                               | URL                                                                                                    |
| ----------------------------- | ------------------------------------------------------------------------------------------------------ |
| **Base URL API**              | `https://ngumpulyuk-backend.onrender.com/api/v1/`                                                      |
| **Dokumentasi API (Swagger)** | [https://ngumpulyuk-backend.onrender.com/docs/api/](https://ngumpulyuk-backend.onrender.com/docs/api/) |

## Deskripsi

Backend ini menyediakan autentikasi (email + Google OAuth), manajemen event & komunitas, diskusi (thread/komentar/like), rekomendasi, notifikasi, integrasi chat LLM (Gemini), serta data wilayah administrasi Indonesia (514 kabupaten/kota) untuk pemilihan lokasi event.

Arsitektur mengikuti domain Django apps (`authentication`, `events`, `communities`, `discussions`, `chat`, dll.) dengan Django REST Framework dan dokumentasi OpenAPI (Swagger/ReDoc).

## Fitur utama

| Modul               | Fitur                                                                 |
| ------------------- | --------------------------------------------------------------------- |
| **Autentikasi**     | Register, login JWT, verifikasi email, reset password, Google OAuth   |
| **Users**           | Profil, onboarding (minat & preferensi), aktivitas                    |
| **Events**          | CRUD event, join/leave, kategori, filter & pagination, upload cover   |
| **Communities**     | Circle, member, admin, join/leave                                     |
| **Discussions**     | Thread global & per circle, komentar, like                            |
| **Notifications**   | In-app notifications, blast (staff)                                   |
| **Chat (Ngumpsky)** | Percakapan AI, rekomendasi event/circle, monitoring & koreksi (admin) |
| **Recommendations** | Sinyal & rekomendasi event                                            |
| **Common**          | Landing public stats, daftar lokasi Indonesia, seed data sintetis     |

## Teknologi

- **Python 3.9+**
- **Django 4.2** + **Django REST Framework**
- **PostgreSQL** (Supabase) via `DATABASE_URL`
- **JWT** — `djangorestframework-simplejwt`
- **API docs** — `drf-spectacular` ([Swagger production](https://ngumpulyuk-backend.onrender.com/docs/api/))
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

Buat file **`.env`** di root backend. Salin variabel berikut dan isi nilainya:

```env
SECRET_KEY=generate-a-strong-secret-key
DEBUG=True
DJANGO_ENV=development
ALLOWED_HOSTS=localhost,127.0.0.1

DATABASE_URL=postgresql://USER:PASSWORD@HOST:6543/postgres

FRONTEND_URL=http://localhost:5173

EMAIL_HOST_USER=mailtrap-user
EMAIL_HOST_PASSWORD=mailtrap-password

GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
SOCIAL_AUTH_PASSWORD=random-string-for-social-users
```

### 3. Migrasi database

```bash
python manage.py migrate
```

### 4. (Opsional) Superuser & seed sintetis

```bash
python manage.py createsuperuser

# Data demo
python manage.py seed_synthetic_data --clear
```

### 5. Jalankan server

```bash
python manage.py runserver
```

**Lokal**

|              | URL                               |
| ------------ | --------------------------------- |
| Base URL API | `http://127.0.0.1:8000/api/v1/`   |
| Swagger      | `http://127.0.0.1:8000/docs/api/` |

## API lokasi (kabupaten/kota)

Daftar **514 kabupaten/kota** di Indonesia (Kemendagri 2026 + koordinat).

| Query    | Default | Keterangan                                        |
| -------- | ------- | ------------------------------------------------- |
| `search` | —       | Filter nama kab/kota, provinsi, atau kode wilayah |
| `limit`  | `50`    | Maks hasil per request (1–514)                    |

**Ambil data **

```bash
# Production — 50 kota pertama
curl "https://ngumpulyuk-backend.onrender.com/api/v1/locations/"

# Cari nama
curl "https://ngumpulyuk-backend.onrender.com/api/v1/locations/?search=bandung"
curl "https://ngumpulyuk-backend.onrender.com/api/v1/locations/?search=jakarta&limit=20"

# Semua 514 kab/kota
curl "https://ngumpulyuk-backend.onrender.com/api/v1/locations/?limit=514"

# Lokal
curl "http://127.0.0.1:8000/api/v1/locations/?search=surabaya"
```

**Update data lokasi**

Regenerasi file JSON dari sumber Kemendagri terbaru:

```bash
python scripts/generate_indonesia_locations.py
```

## Endpoint berguna

Path relatif terhadap base URL (`/api/v1/`). Coba langsung di [Swagger](https://ngumpulyuk-backend.onrender.com/docs/api/).

| Path                      | Keterangan                                                               |
| ------------------------- | ------------------------------------------------------------------------ |
| `GET /public/landing/`    | Data landing (stats, spotlight)                                          |
| `GET /locations/`         | Kabupaten/kota Indonesia — lihat [API lokasi](#api-lokasi-kabupatenkota) |
| `GET /events/categories/` | Kategori event                                                           |
| `POST /auth/register/`    | Registrasi                                                               |
| `POST /chat/`             | Chat Ngumpsky                                                            |

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
