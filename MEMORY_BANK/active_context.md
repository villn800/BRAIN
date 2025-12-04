# Active Context & Log Pointer

## Current Snapshot

- Repo: `villn800/BRAIN`
- v1 is **shipped**:
  - Backend initiatives (H1–H6) complete.
  - Frontend UX (H7) complete.
  - Ops/observability/deployment (H8) complete.
- Initiative 6 (Studio board refresh) in progress:
  - Inputs rail left; board hero + header on right with inline Settings + Refresh.
  - Settings expanded (grid density, thumb size, overlay, theme intensity soft/bold, motion standard/reduced) with localStorage + defaults respecting reduced motion.
  - Studio gradient theme + tokens applied to backgrounds, cards, masonry tiles, detail panel, and settings dialog; motion-safe hover tuning.
  - Settings dialog layout tightened (two-column options, keyboard trap, reset) after hook-order fix.
  - Playbook v2 dashboard updated; README text refreshed for new layout/theme (screenshots pending).
- Initiative 8 (Twitter media vs avatars + Delete) underway:
  - Twitter extractor gathers multiple candidates (og:image, twitter:image, JSON-LD) and demotes `/profile_images/` avatars in favor of `/media/` or card images.
  - Fixtures for tweets live in `backend/tests/fixtures/twitter/` to keep regression tests honest.
  - New delete flow: `items_service.delete_item_and_assets` plus storage `safe_remove_path` and `DELETE /api/items/{id}`; detail panel has a Delete button.
- Static assets:
  - Stored under `STORAGE_ROOT`.
  - Served via FastAPI at `/assets`.
- Tests:
  - Backend: `cd APP_/backend && source .venv/bin/activate && python -m pytest` → 52 passing (new `.venv` created via `python -m venv .venv && pip install -r requirements.txt`).
  - Frontend: `npm run build` succeeds.
- Deployment:
  - Docker Compose stack present but may still need real‑world testing on Unraid or similar.
  - `.env.example` documents environment and ports.

## Log Pointer

Longer‑term decisions and history are tracked in `log.md` in this memory bank.  
When major milestones or initiative close‑outs happen, append a 3‑4 line entry at the top of `log.md`.
