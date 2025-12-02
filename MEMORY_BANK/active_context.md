# Active Context & Log Pointer

## Current Snapshot

- Repo: `villn800/BRAIN`
- v1 is **shipped**:
  - Backend initiatives (H1–H6) complete.
  - Frontend UX (H7) complete.
  - Ops/observability/deployment (H8) complete.
- Static assets:
  - Stored under `STORAGE_ROOT`.
  - Served via FastAPI at `/assets`.
- Tests:
  - Backend: `python -m pytest` → 51 passing tests, no warnings after pypdf switch.
  - Frontend: `npm run build` succeeds; `npm audit` reports 0 vulnerabilities.
- Deployment:
  - Docker Compose stack present but may still need real‑world testing on Unraid or similar.
  - `.env.example` documents environment and ports.

## Log Pointer

Longer‑term decisions and history are tracked in `log.md` in this memory bank.  
When major milestones or initiative close‑outs happen, append a 3‑4 line entry at the top of `log.md`.
