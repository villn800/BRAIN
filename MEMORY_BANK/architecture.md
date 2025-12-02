# Architecture Notes – Backend & Frontend

## Backend (FastAPI)

Location: `APP_/backend`

- `app/main.py`
  - `create_app()` and lifespan.
  - Mounts static assets: `/assets` → `STORAGE_ROOT`.
  - Includes versioned API router under `API_V1_PREFIX` (usually `/api`).

- `app/core/config.py`
  - Pydantic v2 `Settings` with `ConfigDict`.
  - Key env vars:
    - `PROJECT_NAME`, `API_V1_PREFIX`
    - `DATABASE_URL`
    - `STORAGE_ROOT`
    - `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`
    - `MAX_UPLOAD_BYTES`, thumbnail/PDF limits
    - `LOG_LEVEL`, `ENVIRONMENT`, `APP_VERSION`
    - `VITE_API_BASE_URL`, `VITE_ASSET_BASE_URL` when needed.

- `app/core/security.py`
  - `hash_password`, `verify_password`.
  - `create_access_token`, `decode_access_token`.
  - `get_current_user` dependency using JWT `Authorization: Bearer`.

- `app/core/storage.py`
  - Helpers for building **relative** paths under `STORAGE_ROOT`.
  - `FileWriteGuard` to clean up partially‑written files on failure.
  - Guards against path traversal outside `STORAGE_ROOT`.

- `app/core/logging.py`
  - Centralized logger with UTC timestamps and environment/version metadata.
  - Structured-ish events for auth, ingestion, upload, tagging.

- `app/models.py`
  - `User`
  - `Item` (UUID id, enums for type/status, URL + file metadata, origin_domain).
  - `Tag` + `ItemTag` many‑to‑many.
  - Timezone‑aware timestamps (UTC).

- `app/schemas.py`
  - Pydantic v2 models for:
    - Auth, tokens.
    - Item create/update/out.
    - Tag payloads.
    - URL ingestion + upload payloads.
    - Search / filter parameters where modeled.

- `app/api/auth.py`
  - `POST /api/auth/bootstrap` – create first admin.
  - `POST /api/auth/login` – JWT login.

- `app/api/items.py`
  - CRUD: `GET/POST/PATCH/DELETE /api/items`.
  - `POST /api/items/{id}/tags` – replace tags.
  - `POST /api/items/url` – ingest URLs.
  - `POST /api/items/upload` – file uploads.

- `app/services/*`
  - `items_service.py` – core item CRUD, filters, tag ops.
  - `ingestion_service.py` – URL ingestion orchestration + preview image download.
  - `file_processing.py` – image/pdf pipelines (thumbnails, text extraction).
  - `metadata_service.py`, `url_extractors.py` – generic + Twitter/Pinterest metadata via BeautifulSoup.

## Frontend (React/Vite)

Location: `APP_/frontend`

- `src/main.jsx`
  - Renders `<App />` and wraps with providers (e.g., AuthContext).

- `src/App.jsx`
  - Sets up routes:
    - `/login`
    - `/` (items grid)
    - `/items/:id` (detail view)
  - Uses auth context to guard private routes.

- `src/context/AuthContext.jsx`
  - Stores JWT token + user state.
  - Persists session (e.g., localStorage).
  - Exposes `login`, `logout`, `isAuthenticated`.

- `src/lib/api.js`
  - API client with base URL (often `/api`).
  - Attaches `Authorization: Bearer <token>` automatically.
  - Helpers: `login`, `getItems`, `createItemFromUrl`, `uploadItem`, `updateItem`, `updateItemTags`.

- `src/lib/assets.js`
  - Builds URLs from `VITE_ASSET_BASE_URL` + relative paths from backend.

- `src/components/*` and `src/pages/*`
  - Login form, grid, item card, detail layout.
  - Save‑link and upload forms.
  - Search/filter controls + pagination.

- `src/styles.css`
  - Overall theme:
    - Clean, light, desktop‑first.
    - Centered login card (screenshot).
    - Card grid + detail view styling.
