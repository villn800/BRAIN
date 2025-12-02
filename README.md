# BRAIN – Inspiration Vault

BRAIN is a self-hostable **Inspiration Vault / moodboard**:

- Save **URLs** (generic web, Twitter/X, Pinterest).
- **Upload images and PDFs**.
- Normalize URLs and fetch metadata + preview images.
- Store everything in a structured DB with tags, types, and text content.
- Browse everything through a **login-gated web UI** with:
  - Grid of items with thumbnails.
  - Detail view with metadata & preview.
  - Search and filters (text, type, tags, date).
  - “Save link” and “Upload file” flows.

The v1 backend, frontend, ingestion, search/filtering, and Docker setup are complete and closed out. This README describes how to run and extend that system.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)  
2. [Prerequisites](#prerequisites)  
3. [Configuration](#configuration)  
4. [Running Locally (dev)](#running-locally-dev)  
5. [Docker / Compose](#docker--compose)  
6. [Using the App](#using-the-app)  
7. [Key API Endpoints](#key-api-endpoints)  
8. [Testing & Quality](#testing--quality)  
9. [Project Conventions](#project-conventions)  
10. [Backlog / Future Ideas](#backlog--future-ideas)

---

## Architecture Overview

### Backend

Located in `APP_/backend`.

- **Framework:** FastAPI
- **ORM:** SQLAlchemy
- **Validation:** Pydantic v2
- **Migrations:** Alembic
- **Auth:** JWT with bootstrap + login
- **Storage:** Files under `STORAGE_ROOT` (relative paths in DB), served at `/assets`
- **Observability:**
  - Centralized UTC logging (configurable `LOG_LEVEL`)
  - `/health` endpoint with environment/version/timestamp diagnostics

Key modules:

- `app/main.py`
  - `create_app()` and lifespan.
  - Mounts static assets: `/assets` → `STORAGE_ROOT`.
  - Includes versioned API under `API_V1_PREFIX` (usually `/api`).

- `app/core/config.py`
  - Pydantic `Settings` using `ConfigDict`.
  - Reads env vars such as:
    - `ENVIRONMENT`, `APP_VERSION`, `PROJECT_NAME`, `API_V1_PREFIX`
    - `DATABASE_URL`
    - `STORAGE_ROOT`
    - `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`
    - `MAX_UPLOAD_BYTES`, thumbnail/PDF text limits
    - `LOG_LEVEL`
    - `VITE_API_BASE_URL`, `VITE_ASSET_BASE_URL` (when relevant)

- `app/core/security.py`
  - Password hashing (`hash_password`, `verify_password`) using bcrypt.
  - JWT helpers (`create_access_token`, `decode_access_token`).
  - `get_current_user` dependency for auth-guarded routes.

- `app/core/storage.py`
  - Builds safe **relative** paths under `STORAGE_ROOT`.
  - `FileWriteGuard` to track created files and delete them on failure.
  - Guards against writing outside `STORAGE_ROOT`.

- `app/core/logging.py`
  - Centralized `logging` config.
  - Emits structured events with UTC timestamps, environment, and app version.

- `app/database.py`
  - SQLAlchemy engine + session factory.
  - `get_db()` dependency with proper cleanup.

- `app/models.py`
  - `User` – auth user.
  - `Item` – core content entity:
    - UUID id
    - `type` enum (e.g. url, image, pdf, etc.)
    - `status` enum
    - URL + file metadata
    - `origin_domain`
    - `created_at` / `updated_at` (timezone-aware UTC)
  - `Tag`, `ItemTag` – many-to-many tagging per user.
  - Alembic migrations live in `backend/alembic/versions/`.

- `app/schemas.py`
  - Pydantic models for:
    - Auth payloads & token responses.
    - Items (create, update, out).
    - Tags & tag assignment.
    - URL ingestion + upload payloads.
    - Search/filter parameters (where modeled).

- `app/api/auth.py`
  - `POST /api/auth/bootstrap` – one-time admin creation.
  - `POST /api/auth/login` – login, returns JWT.

- `app/api/items.py`
  - `GET /api/items` – list, search, filter, paginate items.
  - `POST /api/items` – create item.
  - `PATCH /api/items/{id}` – update.
  - `DELETE /api/items/{id}` – delete.
  - `POST /api/items/{id}/tags` – replace tags.
  - `POST /api/items/url` – ingest a URL (generic/Twitter/X/Pinterest).
  - `POST /api/items/upload` – upload image/PDF with validation.

- `app/services/*`
  - `items_service.py` – business logic for CRUD, filtering, tagging.
  - `ingestion_service.py` – URL ingestion orchestration & preview image download.
  - `file_processing.py` – upload pipelines (images → thumbnails, PDFs → text via **pypdf**).
  - `metadata_service.py`, `url_extractors.py` – generic + domain-specific metadata extraction using BeautifulSoup.

---

### Frontend

Located in `APP_/frontend`.

- **Framework:** React (function components + hooks)
- **Bundler:** Vite 7.x
- **Routing:** `react-router-dom`
- **Styling:** `src/styles.css` (clean, desktop-first theme)

Key pieces:

- `src/main.jsx`  
  Mounts `<App />` and wraps with context providers.

- `src/App.jsx`  
  - Configures routes:
    - `/login` – login page.
    - `/` – grid view.
    - `/items/:id` – item detail.
  - Applies auth guard via `AuthContext`.

- `src/context/AuthContext.jsx`  
  - Holds auth state (JWT token, user info).
  - Persists session (e.g., localStorage).
  - Exposes `login`, `logout`, `isAuthenticated`.

- `src/lib/api.js`  
  - Small API client with base URL (usually `/api`).
  - Automatically attaches `Authorization: Bearer <token>` when logged in.
  - Helpers for:
    - `login`
    - `getItems` (search, filters, pagination)
    - `createItemFromUrl`
    - `uploadItem`
    - `updateItem`
    - `updateItemTags`

- `src/lib/assets.js`  
  - Builds full URLs from `VITE_ASSET_BASE_URL` + relative paths from backend (e.g., `uploads/thumbnails/...`).

- `src/components/*`, `src/pages/*`  
  - Login card (“BRAIN Inspiration Vault”).
  - Item grid + cards.
  - Detail view layout.
  - Search/filter controls.
  - Save-link and upload forms.
  - Pagination controls.

---

## Prerequisites

For **local dev (non-Docker)**:

- **Python:** 3.11+ (virtualenv recommended)
- **Node:** 20.19+ or 22.12+ (required for Vite 7)
- **Postgres** (recommended) or SQLite for local play
- **Git**

For **Docker / Compose**:

- Docker Engine or Docker Desktop  
- docker compose plugin (`docker compose …`)

---

## Configuration

Important env vars are documented in `.env.example` under `APP_`.

Backend (via `app/core/config.py`) uses:

- **Runtime**
  - `ENVIRONMENT` – `development` or `production`
  - `APP_VERSION` – arbitrary version string (also appears in logs and `/health`)

- **API / App**
  - `PROJECT_NAME`
  - `API_V1_PREFIX` (default `/api`)

- **Database**
  - `DATABASE_URL` – e.g. `postgresql+psycopg2://user:pass@host:5432/brain`

- **Auth**
  - `SECRET_KEY`
  - `ACCESS_TOKEN_EXPIRE_MINUTES`

- **Storage & Upload**
  - `STORAGE_ROOT` – absolute path inside container/host where files are stored.
  - `MAX_UPLOAD_BYTES` – maximum upload size.
  - Thumbnail + PDF extraction limits.

- **Logging**
  - `LOG_LEVEL` – `INFO`, `DEBUG`, etc.

Frontend (Vite) uses:

- `VITE_API_BASE_URL` (if set; otherwise client may assume `/api`)
- `VITE_ASSET_BASE_URL` – typically the backend `/assets` URL (e.g. `http://localhost:4000/assets`)
- `FRONTEND_PORT` – port exposed by Docker for the frontend service

**Static assets:**  
FastAPI mounts `STORAGE_ROOT` at `/assets`, so relative paths stored in the DB become accessible as:
`<VITE_ASSET_BASE_URL>/<relative_path>`.

---

## Running Locally (dev)

### 1. Backend

From `APP_/backend`:

```bash
# (optional) create a venv one level up
cd APP_
python -m venv .venv
source .venv/bin/activate

cd backend

# Install deps
pip install -r requirements.txt

# Run migrations (dev DB)
python -m alembic upgrade head

# Start API server
python -m uvicorn app.main:create_app --reload --host 0.0.0.0 --port 4000
