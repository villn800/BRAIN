# Memory Log

Append new entries at the **top** (most recent first).

---

## 2025-12-08 – Pinterest pin metadata resilience

- Hardened Pinterest extractor with twitter/og fallbacks, generic metadata promotion to pins, gate-page flagging (`extra.pinterest_gate`), and browser-like fetch headers; added logging for Pinterest fetches (status/length/prefix).
- Captured fixtures for real pins, gate pages, and generic metadata; added debug helper `python -m scripts.pinterest_debug '<pin_url>'` plus README docs. Backend tests: `cd APP_/backend && python -m pytest -q` (79 passing; passlib crypt warning).

## 2025-12-06 – Initiative 4: Twitter video UX & docs refinement

- Frontend states clarified: inline MP4 keeps “Video” badge/player; HLS-only/non-playable tweets show image with “Video on X” badge and “Play on X” link/callout; text/image-only still expose an “Open on X” path. Backend logic unchanged.
- Docs updated (APP_/README.md, APP_/backend/README.md) to describe UX states, HLS-only flag meaning, and escape hatches.
- Build check: `cd APP_/frontend && npm run build` (vite) succeeded; backend pytest remains green from prior runs (no backend changes).

## 2025-12-06 – Initiative 2: Twitter headless HLS-only tagging (detection only)

- Added metadata flag `twitter_hls_only=true` when `.m3u8` is observed (static meta or headless) and no MP4 is selected; `media_kind` stays `image`, `video_url` unset. Headless logs `outcome=hls_only`; static extractor logs “observed HLS-only”.
- Tests extended: extractor HLS fixture asserts flag, headless HLS-only responses return the flag, ingestion persists it; MP4 ingestion asserts flag absent. Commands: `python -m pytest tests/test_url_extractors.py tests/test_twitter_headless.py tests/test_url_ingestion.py -q` and full `python -m pytest -q` (74 passed, passlib warning only).
- Docs updated (README + backend README) to describe `twitter_hls_only` meaning and that playback remains unchanged for v1.

## 2025-12-06 – Initiative 3: Twitter headless observability & debug tools

- Added structured logging to `app/services/twitter_headless.py` (start/outcome/candidate counts, debug candidate list, error stack) to make headless runs explainable from logs alone.
- Introduced CLI probe `python -m scripts.twitter_headless_debug '<tweet_url>' [--timeout 15] [--log-level DEBUG]` for quick, out-of-band checks (returns exit 0 on success, 1 otherwise).
- No HTTP debug endpoint added (no existing pattern); relying on CLI + logs. Full backend pytest still required as gate.

## 2025-12-05 – Initiative 1: Twitter headless video URL detection & normalization

- Static extractor + headless resolver now accept `video.twimg.com` MP4 URLs with query params (`.mp4?tag=NN`); HLS-only remains image-only for v1.
- Tests updated: `_pick_best_video`, headless resolver, and ingestion now cover MP4-with-query; full suite `python -m pytest -q` passes (73 tests).
- Frontend detail/card includes debug hooks (`ItemDetailPanel` console log, `data-testid` on video player/badge) and manual smoke-test steps documented in `DOCS_/_playbook/twitter_headless_video_url_fix_playbook.md`.

## 2025-12-04 – Initiative 9: Twitter headless video fallback (option C)

- Added gated config flags `TWITTER_HEADLESS_ENABLED` (default off) and `TWITTER_HEADLESS_TIMEOUT_SECS`; documented optional Playwright install (`requirements-headless.txt`, `python -m playwright install`).
- Implemented headless resolver (`app/services/twitter_headless.py`) sniffing `video.twimg.com` network responses, preferring MP4; logs when Playwright missing or no media.
- Integrated into `_extract_twitter` behind flag + `/status/` check; ingestion test ensures headless video extra persisted; extractor tests cover flag-on/off; Playwright import remains optional when disabled.
- Tests: `cd APP_/backend && python -m pytest` → 71 passing.

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
