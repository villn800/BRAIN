# Workflow & Deployment

## Local Dev – Backend

From `APP_/backend`:

```bash
# Run tests
python -m pytest

# Run dev server (uses .venv python)
../.venv/bin/python -m uvicorn app.main:create_app --reload --host 0.0.0.0 --port 4000

# Health check
curl http://localhost:4000/health
```

Bootstrap admin (first time in a new DB):

```bash
curl -X POST http://localhost:4000/api/auth/bootstrap   -H "Content-Type: application/json"   -d '{
    "email": "admin@example.com",
    "username": "moodboard-admin",
    "password": "changeme123"
  }'
```

Then log in via the web UI with the same credentials.

## Local Dev – Frontend

From `APP_/frontend`:

```bash
npm install            # Node 20.19+ recommended (Vite 7)
npm run dev            # dev server
npm run build          # production build
npm audit              # should be 0 vulnerabilities
```

Typically:
- Frontend dev server on port 5173.
- Backend on port 4000.

## Environment & Storage

Key env vars (backend):

- `ENVIRONMENT` – `development` or `production`.
- `APP_VERSION`
- `DATABASE_URL`
- `STORAGE_ROOT` – filesystem base for files/thumbnails.
- `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- `MAX_UPLOAD_BYTES` and thumbnail/PDF limits.
- `LOG_LEVEL`

Assets:

- All files are stored under `STORAGE_ROOT` and served at `/assets`.
- Frontend uses `VITE_ASSET_BASE_URL` (e.g., `http://localhost:4000/assets`).

## Docker / Compose

From `APP_/deploy`:

```bash
docker compose up --build
```

Stack usually includes:

- Postgres
- Backend (FastAPI + uvicorn)
- Frontend (Vite dev or built static server)
- Volumes for DB and `STORAGE_ROOT`

Default URLs (subject to `.env`):

- Backend: `http://localhost:4000`
- Health: `http://localhost:4000/health`
- Assets: `http://localhost:4000/assets/...`
- Frontend: `http://localhost:${FRONTEND_PORT}`

Ensure the host directory mapped to `STORAGE_ROOT` exists and is writable.
