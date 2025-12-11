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

## Optional: headless Twitter video fallback
- Controlled by env vars: `TWITTER_HEADLESS_ENABLED` (default `false`) and `TWITTER_HEADLESS_TIMEOUT_SECS` (default `15.0` seconds).
- Only install the optional dependency when enabling the flag:
  ```bash
  pip install -r requirements-headless.txt
  python -m playwright install
  ```
- When enabled, the resolver accepts `video.twimg.com` MP4 URLs even when query params are present (e.g. `.mp4?tag=NN`) and still prefers MP4 over HLS; HLS-only tweets remain image-only for v1.
- The backend still runs and tests pass without Playwright installed when the feature is disabled.

## Twitter headless debug tools
- Structured logs: search for `twitter_headless` messages showing start → candidates → outcome (includes counts and chosen type; debug logs list captured URLs).
- CLI: `python -m scripts.twitter_headless_debug 'https://x.com/.../status/...' [--timeout 15] [--log-level DEBUG]` (requires optional Playwright install). Exit code `0` on success, `1` on no video/timeout.
- HLS-only tagging: when only `.m3u8` variants are seen and no MP4 is selected, `extra["twitter_hls_only"]=True` (still `media_kind="image"` and no `video_url` in v1). Logged as `outcome=hls_only` for headless or `observed HLS-only` for static extractor.
- UX expectations: inline video appears only for MP4; HLS-only/non-playable tweets render as image with a “Video on X” badge in the grid and “Play on X” link in detail; backend behaviour is unchanged.

## Pinterest support & debug
- Pinterest URLs use a domain-specific extractor that looks for `og`/`twitter` meta tags (title/description/image) and classifies items as `pin` even when metadata is partial.
- When Pinterest returns a consent/login/bot gate page without tags, the fetcher logs `pinterest_fetch ...` with status/length/prefix and marks the response with `extra["pinterest_gate"]=True`; those ingest as plain URLs.
- Generic metadata is promoted to a pin when available for Pinterest pages; otherwise the title may fall back to the normalized URL.
- Debug helper: `python -m scripts.pinterest_debug '<pin_url>' [--timeout 8] [--log-level DEBUG]` prints status, classification, and any title/image detected (no DB writes).

## Tests

Run the backend unit tests (uses pytest + FastAPI TestClient):

```bash
cd /Users/robot1/Downloads/CURSOR_/BRAIN_/APP_/backend
pytest
```
