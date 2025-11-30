# Backend (FastAPI)

This directory contains the FastAPI + SQLAlchemy backend for the BRAIN Inspiration Vault. The application entrypoint is `app.main:app`, which exposes all routers via the `create_app()` factory and is ready for ASGI servers such as Uvicorn or Hypercorn.

## Run backend locally (no Docker)

```bash
cd /Users/robot1/Downloads/CURSOR_/BRAIN_/APP_/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 4000 --reload
```

Create a `.env` file (or copy `.env.example`) in this directory so `app/core/config.py` can load the core settings:

```bash
cp .env.example .env
# then edit PROJECT_NAME, DATABASE_URL, STORAGE_ROOT, SECRET_KEY, etc.
```

> When using Docker Compose (`APP_/deploy/docker-compose.yml`), the backend container reads environment variables from `APP_/deploy/.env`. Keep the values in sync with `backend/.env` for a smooth local/dev parity.

## Tests

Run the backend unit tests (uses pytest + FastAPI TestClient):

```bash
cd /Users/robot1/Downloads/CURSOR_/BRAIN_/APP_/backend
pytest
```

