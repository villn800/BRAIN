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
- Frontend: `VITE_API_BASE_URL` (default `/api`), `VITE_ASSET_BASE_URL` (default `/assets/`).

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
- `GET /api/items` (search/filter/paginate) · `GET /api/items/{id}`
- `POST /api/items/url` (ingest URL) · `POST /api/items/upload` (image/PDF)
- `PUT /api/items/{id}/tags` (replace tags)
- Static assets: `/assets/<relative_path>`

## 🧪 Quality
- Backend: `python -m pytest`
- Frontend: `cd APP_/frontend && npm run build`

## 📜 Notes
- Settings are per-browser (localStorage) and do not touch backend schema.
- Masonry uses CSS columns for lightweight packing; can be swapped for JS layout later if drag/drop is added.
- ADR for the masonry/panel/settings decision: `docs/_playbook/ADR_masonry_panel.md`.
