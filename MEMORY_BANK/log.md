# Memory Log

Append new entries at the **top** (most recent first).

---

## 2025-12-05 – Initiative 6: Studio Board Layout & Theme

- Refactored board layout: inputs rail on the left, Inspiration Board hero on the right with inline Settings + Refresh; header copy tightened.
- Expanded settings (density, thumb height, overlay mode, theme intensity soft/bold, motion standard/reduced) with defensive localStorage + reset defaults; motion honors reduced-motion.
- Applied studio gradient theme and tokens across background, cards, masonry tiles, detail panel, and settings dialog; hover/focus tuned with motion-safe variants.
- Fixed settings modal hook order and layout (two-column options aligned; keyboard trap intact).
- Tests: `npm run build` (frontend) passed; backend pytest now run from a new `.venv` (`cd APP_/backend && source .venv/bin/activate && python -m pytest`) with 52 passing.

## 2025-12-05 – Initiative 8: Twitter Media Heuristics + Delete Flow

- Twitter/X extractor now collects all candidates (og:image, twitter:image, JSON-LD), demotes `/profile_images/` avatars, prefers `/media`/card images, and retains avatar in `metadata.extra`; fixtures added under `backend/tests/fixtures/twitter/`.
- Ingestion tests verify juniorkingpp/girlflours media selection; README documents “prefer media over avatars.”
- Delete flow shipped: `items_service.delete_item_and_assets` + `storage.safe_remove_path`, `DELETE /api/items/{id}`; frontend detail overlay wired with Delete confirm/inline errors, API client handles empty responses.
- Tests: `cd APP_/backend && python -m pytest` → 62 passing; `cd APP_/frontend && npm run build` succeeds.

## 2025-11-30 – v1 Close-Out

- Completed Initiatives 1–4 from `BRAIN_MASTER_PLAYBOOK.md` plus deployment close‑out.
- Backend: ingestion, upload, search/filter/tagging, logging, `/health`, `/assets` all stable; pytest passes with 51 tests.
- Frontend: React/Vite app shipping login, grid, detail, save‑link, upload, filters, pagination; npm audit = 0 vulns.
- Docker Compose: stack for DB + backend + frontend; README and env examples updated.
- `BRAIN_MASTER_PLAYBOOK.md` archived as v1 reference; future work moves into focused playbooks (e.g., Collections & Favorites, Semantic Search).

## 2025-12-03 – Initiative 5: Masonry UI & Settings

- Rebuilt the home experience into a Pinterest-style masonry board with sticky command rail (search/filters/save/upload) to keep the grid above the fold.
- Added hover overlays, adjustable density/thumbnail size/overlay mode via a settings modal backed by localStorage; settings context introduced.
- Click opens a right-side detail panel driven by `?itemId=`; `/items/:id` remains for deep links; keyboard/ESC/focus trap supported.
- README refreshed with new flows; ADR documented at `docs/_playbook/ADR_masonry_panel.md`; frontend build green (`npm run build`).
