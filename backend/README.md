# Backend (FastAPI)

This directory contains the FastAPI + SQLAlchemy backend for the BRAIN Inspiration Vault. The application entrypoint is `app.main:app`, which exposes all routers via the `create_app()` factory and is ready for ASGI servers such as Uvicorn or Hypercorn.

## Run backend locally (no Docker)

```bash
cd /Users/robot1/Downloads/CURSOR_/BRAIN_/APP_/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 4000 --port 4000 --reload
```

Set the required environment variables (e.g., `DATABASE_URL`, `STORAGE_ROOT`, `SECRET_KEY`) before starting Uvicorn or create a `.env` file that matches the `Settings` class in `app/core/config.py`.

