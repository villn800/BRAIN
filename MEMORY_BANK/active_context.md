# Active Context & Log Pointer

## Current Snapshot

- Repo: `villn800/BRAIN`
- v1 is **shipped**:
  - Backend initiatives (H1–H6) complete.
  - Frontend UX (H7) complete.
  - Ops/observability/deployment (H8) complete.
- Initiative 6 (Studio board refresh) in progress (UI polish/screenshot tasks pending).
- Initiative 8 (Twitter media vs avatars + Delete) completed:
  - Twitter extractor gathers multiple candidates (og:image, twitter:image, JSON-LD), demotes `/profile_images/` avatars, and picks `/media`/card images; avatar is kept in `metadata.extra`.
  - Fixtures for tweets live in `backend/tests/fixtures/twitter/`; ingestion tests assert media chosen for juniorkingpp/girlflours.
  - Delete flow shipped: `items_service.delete_item_and_assets` + `storage.safe_remove_path`, `DELETE /api/items/{id}`; detail overlay Delete button wired with confirm + inline errors and board removal; API client handles empty DELETE responses.
  - Docs/playbook/README updated; social extractor backlog added; tests green (`python -m pytest`, `npm run build`).
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
