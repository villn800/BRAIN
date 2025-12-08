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
- Initiative 9 (Twitter headless video fallback) in flight:
  - Config flags added: `TWITTER_HEADLESS_ENABLED` (default false) and `TWITTER_HEADLESS_TIMEOUT_SECS` (default 15s); optional dependency bundle `requirements-headless.txt` with Playwright install instructions.
  - Headless resolver (`services/twitter_headless.py`) sniffs `video.twimg.com` responses via Playwright; prefers `.mp4`, falls back to `.m3u8`/hls; logs when Playwright missing or no media.
  - `_extract_twitter` calls headless path only when flag enabled, `/status/` path, and no existing video metadata; updates `metadata.extra` and optional poster.
  - Tests added: `tests/test_twitter_headless.py`, extractor flag-on/off coverage, ingestion test ensuring video extras persisted.
- Initiative 1 (Twitter headless video URL detection & normalization) completed:
  - Static extractor `_pick_best_video` now accepts `video.twimg.com` MP4 URLs even when query params are present (e.g. `.mp4?tag=21`); HLS-only still treated as image-only for v1.
  - Headless resolver accepts `.mp4`/`.m3u8` paths with query params, still preferring MP4; ingestion path persists `extra.media_kind="video"` with query-bearing MP4 URLs.
  - Frontend detail/card surfaces include lightweight debug hooks (`ItemDetailPanel` console log, `data-testid` for video player/badge) to aid manual verification.
- Initiative 2 (Twitter headless HLS-only handling) completed for tagging:
  - HLS-only detection: if `.m3u8` seen (static meta or headless) and no MP4 selected, set `extra.twitter_hls_only=true`; keep `media_kind="image"` and no `video_url` persisted.
  - Headless logs `outcome=hls_only`; static extractor logs “observed HLS-only”; headless MP4 success clears the flag.
- Initiative 3 (Twitter headless observability) in progress:
  - Structured logging emits `twitter_headless_start` and `outcome=...` with candidate counts; debug log lists captured URLs.
  - CLI probe: `python -m scripts.twitter_headless_debug '<tweet_url>' [--timeout 15] [--log-level DEBUG]` (requires Playwright install); exit 0 on success, 1 on no video.
  - No debug HTTP endpoint added (no existing pattern); rely on CLI + logs.
- Initiative 4 (Twitter video UX & docs refinement) completed:
  - UI states: inline MP4 shows “Video” badge and player; HLS-only/non-playable shows image with “Video on X” badge and “Play on X” link; image/text-only still show “Open on X” where relevant.
  - Backend unchanged; `twitter_hls_only` remains metadata-only flag for prevalence tracking.
- Tests:
  - Backend: `cd APP_/backend && python -m pytest` → 71 passing (Playwright optional and not required with flag off).
  - Frontend: `npm run build` succeeds.
- Deployment:
  - Docker Compose stack present but may still need real‑world testing on Unraid or similar.
  - `.env.example` documents environment and ports.

## Log Pointer

Longer‑term decisions and history are tracked in `log.md` in this memory bank.  
When major milestones or initiative close‑outs happen, append a 3‑4 line entry at the top of `log.md`.
