# BRAIN Inspiration Vault (v1.2 Studio Board)

BRAIN is a self-hosted inspiration vault / moodboard for saving URLs, Tweets/Pins, images, and PDFs with rich previews. Initiative 6 layers on a studio-style theme plus refreshed layout and settings (density, sizing, overlay, theme intensity, and motion).

## 🧭 UI at a Glance
- **Board:** Masonry grid and header live on the right as the hero surface; hover overlays show quick metadata. Cards are keyboard-focusable (Enter/Space opens).
- **Command rail:** Inputs column on the left with Search/Filters, Save Link, and Upload cards pinned while you browse.
- **Header controls:** Board title + subtitle sit above the grid with Settings + Refresh inline instead of a standalone refresh card.
- **Detail panel:** Clicking a card opens a slide-in panel (`?itemId=` in URL). ESC/backdrop closes; “Full view →” links to `/items/:id` for deep links.
- **Settings:** Gear icon opens a modal to adjust grid density (compact/cozy/airy), thumbnail height (small/medium/large), overlay mode (hover/always), theme intensity (soft/bold), and motion (standard/reduced). Settings persist in localStorage per browser and “Reset” restores cozy/medium/hover/soft/standard (or reduced if the OS requests it). Dialog is keyboard-friendly (ESC closes; focus trap) with tidy two-column layout.
- **Theme:** Gloven-inspired studio look with soft gradients, elevated cards, blue-purple accent, and motion-safe states (honors reduced-motion + the Motion preference).

## 🏗 Stack
- **Frontend:** React + Vite 7, `react-router-dom`; styles in `APP_/frontend/src/styles.css`.
- **Backend:** FastAPI + SQLAlchemy; serves `/api` and static assets at `/assets` from `STORAGE_ROOT`.
- **Database:** PostgreSQL (dev can use SQLite if desired).
- **Auth:** JWT with bootstrap + login.

## 🚀 Local Development
Prereqs: Node 20.19+ (or 22.12+), Python 3.12+, Docker/Compose (optional).

```bash
cd APP_/frontend
npm install
npm run dev  # VITE_API_BASE_URL defaults to /api
```

Backend (one terminal):
```bash
cd APP_/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Visit `http://localhost:5173`, log in, and:
1) Browse masonry grid, hover overlays, click to open right panel.  
2) Use rail filters (keyword/type/tags/date) and load more.  
3) Save a link (`/api/items/url`) or upload image/PDF (`/api/items/upload`).  
4) Reload with `/?itemId=<id>` to reopen the panel; `/items/:id` still works for full-page detail.

## ⚙️ Configuration
Set in `.env` (see `.env.example`):
- Backend: `DATABASE_URL`, `STORAGE_ROOT`, `SECRET_KEY`, `MAX_UPLOAD_BYTES`, `CORS_ALLOW_ORIGINS`, `LOG_LEVEL`, `APP_VERSION`.
- Backend (optional headless Twitter video): `TWITTER_HEADLESS_ENABLED` (default `false`), `TWITTER_HEADLESS_TIMEOUT_SECS` (default `15.0` seconds).
- Frontend: `VITE_API_BASE_URL` (default `/api`), `VITE_ASSET_BASE_URL` (default `/assets/`).

## 🐦 Twitter video via headless browser (optional)
- The headless resolver is off by default; enable it by setting `TWITTER_HEADLESS_ENABLED=true` (optionally tune `TWITTER_HEADLESS_TIMEOUT_SECS`).
- Install the optional dependency only if you enable the flag:
  ```bash
  cd APP_/backend
  pip install -r requirements-headless.txt
  python -m playwright install
  ```
- With the flag on, the resolver accepts `video.twimg.com` MP4 URLs even when query params are present (e.g. `.mp4?tag=NN`) and still prefers MP4 over HLS; HLS-only tweets remain image-only for v1.
- HLS-only tagging: when only `.m3u8` variants are seen (static or headless) and no MP4 is selected, `extra.twitter_hls_only=true`; `media_kind` stays `image` and no `video_url` is persisted. Useful for measuring prevalence ahead of any HLS support.
- Debugging: structured logs emit `twitter_headless_*` entries (start/outcome/candidate counts); run `python -m scripts.twitter_headless_debug 'https://x.com/.../status/...' [--timeout 15]` from `APP_/backend` for a quick CLI probe (requires Playwright install).
- This feature depends on X/Twitter’s frontend; use it in line with Twitter/X ToS and local law, and expect it may break when their UI changes.

### Twitter media UX states (v1)
- Inline video: shows a `<video>` player + “Video” badge when `extra.video_url` is present (`media_kind="video"`).
- HLS-only or other non-playable tweets: render image-only; badge reads “Video on X”; detail panel offers “Play on X” link and notes that inline playback isn’t supported yet.
- Image/text-only tweets: render image/text without video badge; detail panel still offers “Open on X” when applicable.

## 📂 Project Layout
```
APP_/
├── backend/   # FastAPI app, models, services, API routes
├── frontend/  # React/Vite SPA (masonry board, rail, panel, settings)
├── deploy/    # Docker Compose
└── MEMORY_BANK/ # Working context and log
```

## 🔍 API Quick Reference
- `POST /api/auth/bootstrap` (one-time admin) · `POST /api/auth/login`
- `GET /api/items` (search/filter/paginate) · `GET /api/items/{id}` · `DELETE /api/items/{id}`
- `POST /api/items/url` (ingest URL) · `POST /api/items/upload` (image/PDF)
- `PUT /api/items/{id}/tags` (replace tags)
- Static assets: `/assets/<relative_path>`

## 🧪 Quality
- Backend: `python -m pytest`
- Frontend: `cd APP_/frontend && npm run build`

## 📜 Notes
- Settings are per-browser (localStorage) and do not touch backend schema.
- Twitter/X ingestion prefers tweet media/card images over author avatars when those tags are present; text-only tweets still fall back to avatars.
- Item detail view includes a Delete control that calls `DELETE /api/items/{id}` and removes stored files alongside the DB row.
- Masonry uses CSS columns for lightweight packing; can be swapped for JS layout later if drag/drop is added.
- ADR for the masonry/panel/settings decision: `docs/_playbook/ADR_masonry_panel.md`.
