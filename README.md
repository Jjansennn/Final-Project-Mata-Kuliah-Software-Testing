# Task Management System

[![CI Pipeline](https://github.com/Jjansennn/Final-Project-Mata-Kuliah-Software-Testing/actions/workflows/ci.yml/badge.svg)](https://github.com/Jjansennn/Final-Project-Mata-Kuliah-Software-Testing/actions)
[![Coverage](https://codecov.io/gh/Jjansennn/Final-Project-Mata-Kuliah-Software-Testing/branch/main/graph/badge.svg)](https://codecov.io/gh/Jjansennn/Final-Project-Mata-Kuliah-Software-Testing)
![Python](https://img.shields.io/badge/python-3.11-blue)
![React](https://img.shields.io/badge/react-19-61dafb)
![License](https://img.shields.io/badge/license-MIT-green)
[![Release](https://img.shields.io/github/v/release/Jjansennn/Final-Project-Mata-Kuliah-Software-Testing?include_prereleases)](https://github.com/Jjansennn/Final-Project-Mata-Kuliah-Software-Testing/releases)


Aplikasi web full-stack untuk mengelola task (CRUD) — monorepo dengan backend Flask dan frontend React.

---

## Deskripsi Sistem

Task Management System memungkinkan pengguna membuat, melihat, memperbarui, dan menghapus task melalui antarmuka web yang responsif. Setiap task memiliki judul, deskripsi opsional, deadline opsional, dan status (`pending`, `in_progress`, `done`).

Akses dilindungi autentikasi JWT — setiap pengguna hanya bisa melihat dan mengelola task miliknya sendiri.

---

## Arsitektur Aplikasi

```
task-management-system/
├── src/
│   ├── backend/app/          # Flask REST API
│   │   ├── __init__.py       # Inisialisasi Flask, CORS, error handler global
│   │   ├── models.py         # TaskRepository — query SQLite (users + tasks)
│   │   ├── routes.py         # TaskController — endpoint task + JWT middleware
│   │   ├── services.py       # TaskService — logika bisnis, is_overdue
│   │   ├── validators.py     # Validasi input (title, status, email, password, deadline)
│   │   ├── auth_routes.py    # Endpoint /auth/register dan /auth/login
│   │   └── auth_service.py   # Logika autentikasi, JWT HS256, bcrypt
│   └── frontend/             # React + Vite
│       ├── api/apiClient.js  # Semua HTTP request ke backend
│       ├── components/       # TaskList, TaskCard, TaskForm, StatusBadge
│       │                     # CalendarView, LoginForm, RegisterForm
│       ├── App.jsx           # Root component, auth state, view toggle
│       └── main.jsx
├── tests/
│   ├── backend/
│   │   ├── conftest.py       # Fixtures: test client, SQLite in-memory
│   │   ├── unit/             # Unit test: validators, auth_service, services, models
│   │   └── integration/      # Integration test: auth routes, task routes
│   └── frontend/             # Vitest: semua komponen + ApiClient
├── .github/workflows/ci.yml  # GitHub Actions CI/CD
├── requirements.txt
├── package.json
└── pytest.ini
```

### Alur Request Backend

```
Browser / ApiClient (HTTP)
         │
         ▼
  TaskController  (routes.py)      ← Routing, parsing, format JSON
         │
         ▼
  TaskService     (services.py)    ← Aturan bisnis, orkestrasi, is_overdue
         │         ↘
         │     Validator (validators.py)
         ▼
  TaskRepository  (models.py)      ← Query SQL ke SQLite
         │
         ▼
     SQLite DB (database.db)
```

### Stack Teknologi

| Bagian | Teknologi |
|--------|-----------|
| Backend | Python 3.11, Flask, SQLite |
| Frontend | React 19, Vite |
| Autentikasi | JWT HS256 (PyJWT), bcrypt |
| Backend Tests | pytest, pytest-cov, pytest-mock, Hypothesis |
| Frontend Tests | Vitest, fast-check, Testing Library |
| CI/CD | GitHub Actions |

---

## Menjalankan Aplikasi

### Prasyarat

- Python 3.11+
- Node.js 20+

### Environment Variables

Buat file `.env` di root dan `src/frontend/.env`:

| Variabel | Deskripsi | Contoh |
|----------|-----------|--------|
| `JWT_SECRET_KEY` | Secret key untuk JWT — **wajib diganti di production** | `your-secret-key` |
| `VITE_API_BASE_URL` | Base URL backend API | `http://localhost:5000` |

> Jangan pernah commit nilai `JWT_SECRET_KEY` yang sebenarnya ke repository.

### Backend

```bash
pip install -r requirements.txt
PYTHONPATH=src/backend flask --app app run
```

Backend berjalan di `http://localhost:5000`.

### Frontend

```bash
npm install
npm run dev
```

Frontend berjalan di `http://localhost:3000`.

---

## Menjalankan Tests

### Backend

```bash
# Semua test backend dengan coverage
PYTHONPATH=src/backend pytest --cov=app --cov-report=term-missing
```

### Frontend

```bash
# Single run (tanpa watch mode)
npm run test
```

---

## Strategi Pengujian

### Unit Tests (Backend)

Menguji logika bisnis secara terisolasi — tanpa database atau HTTP call. Menggunakan `pytest-mock`.

- Target: `TaskService`, `AuthService`, `Validator`, `TaskRepository`
- Cakupan: perilaku normal, edge case, dan error handling

### Integration Tests (Backend)

Menguji seluruh alur HTTP → Service → Database menggunakan SQLite in-memory.

- Target: semua endpoint REST API (`/tasks`, `/auth/register`, `/auth/login`)
- Cakupan: semua operasi CRUD, autentikasi, ownership check, dan respons error

### Property-Based Tests

Menggunakan **Hypothesis** (backend) dan **fast-check** (frontend) untuk memverifikasi properti kebenaran sistem dengan ratusan input yang di-generate otomatis.

Contoh properti yang diuji:
- Title valid selalu menghasilkan task dengan `status="pending"`
- String whitespace-only selalu ditolak validator
- Task yang dibuat bisa diambil kembali dengan data identik
- Task yang dihapus tidak bisa diakses lagi (HTTP 404)
- N task di database → `GET /tasks` selalu mengembalikan tepat N elemen

### Frontend Tests

Menggunakan **Vitest** + **Testing Library** dengan mock ApiClient.

- Cakupan: semua komponen React (TaskList, TaskCard, TaskForm, StatusBadge, CalendarView, LoginForm, RegisterForm, App)
- Property test dengan fast-check untuk validasi perilaku komponen

---

## Test Coverage

Target coverage: **100%** pada seluruh kode backend (`src/backend/app/`).

```bash
PYTHONPATH=src/backend pytest --cov=app --cov-report=term-missing --cov-report=html
```

Konfigurasi di `pytest.ini`:

```ini
[pytest]
testpaths = tests/backend
addopts = --cov=app --cov-report=term-missing
```

---

## CI Pipeline

Pipeline otomatis berjalan di **GitHub Actions** pada setiap push dan pull request.

```
Push / Pull Request
        │
        ├── test-backend ──── Install deps → Validate import → pytest + coverage
        │
        └── test-frontend ─── Install deps → Build → Vitest
                │
                └── (kedua job lulus)
                        │
                        └── release (tag release*) ── Buat GitHub Release + tarball
```

| Job | Trigger | Aksi |
|-----|---------|------|
| `test-backend` | Semua push & PR | Install Python deps, validasi import, jalankan pytest + coverage |
| `test-frontend` | Semua push & PR | Install Node deps, build frontend, jalankan Vitest |
| `release` | Tag `release*` (setelah test lulus) | Buat GitHub Release dengan tarball |

---

## Dokumentasi API

Base URL: `http://localhost:5000`

Semua respons menggunakan `Content-Type: application/json`.

Endpoint task memerlukan header `Authorization: Bearer <token>`.

### Model Task

```json
{
  "id": 1,
  "title": "Buat laporan bulanan",
  "description": "Laporan keuangan bulan Juli",
  "status": "pending",
  "deadline": "2026-07-31T17:00:00",
  "is_overdue": false,
  "created_at": "2026-07-01T10:00:00",
  "updated_at": "2026-07-01T10:00:00"
}
```

Nilai `status` yang valid: `pending`, `in_progress`, `done`.

### Auth Endpoints

| Method | Path | Deskripsi | Status Sukses |
|--------|------|-----------|---------------|
| `POST` | `/auth/register` | Daftar akun baru | 201 |
| `POST` | `/auth/login` | Login, dapatkan JWT | 200 |

### Task Endpoints (Protected)

| Method | Path | Deskripsi | Status Sukses |
|--------|------|-----------|---------------|
| `POST` | `/tasks` | Buat task baru | 201 |
| `GET` | `/tasks` | Ambil semua task milik user | 200 |
| `GET` | `/tasks/{id}` | Ambil task by ID | 200 |
| `PUT` | `/tasks/{id}` | Perbarui task | 200 |
| `DELETE` | `/tasks/{id}` | Hapus task | 200 |

### Penanganan Error

| Exception | HTTP Status | Keterangan |
|-----------|-------------|------------|
| `ValueError` | 400 | Input tidak valid |
| `TaskNotFoundError` | 404 | Task tidak ditemukan |
| `PermissionError` | 403 | Task milik user lain |
| JWT tidak valid / kedaluwarsa | 401 | Autentikasi gagal |
| `Exception` | 500 | Kesalahan internal server |
