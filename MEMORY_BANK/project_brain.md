# Project – BRAIN Inspiration Vault

## Concept

BRAIN is a self‑hostable **Inspiration Vault / moodboard**:

- Save **URLs** (generic web, Twitter/X, Pinterest).
- **Upload images and PDFs**.
- Normalize URLs and fetch metadata + preview images.
- Store files under a storage root and index everything with tags, types, and text content.
- Provide a login‑gated web UI to:
  - Browse a **grid** of items with thumbnails.
  - Open a **detail view** with metadata and previews.
  - Run **search and filters** across text, type, tags, date.
  - Save new links and upload assets from the browser.

## Architecture Summary

- **Backend**
  - FastAPI + SQLAlchemy + Pydantic v2.
  - Alembic migrations.
  - JWT auth (bootstrap + login).
  - URL ingestion and upload pipelines.
  - Search / filter / tagging API.
  - Logging + `/health` with environment/version diagnostics.
  - Static assets from `STORAGE_ROOT` served at `/assets`.

- **Frontend**
  - React + Vite SPA.
  - Auth context + guarded routes.
  - Grid & detail views.
  - Save‑link and upload forms.
  - Search/filter UI + pagination.
  - Uses `VITE_ASSET_BASE_URL` to render thumbnails/files.

- **Deployment**
  - Docker Compose stack with Postgres, backend, frontend.
  - `.env.example` documents env vars and ports.
  - v1 is closed out: tests pass, npm audit clean, static assets wired.
