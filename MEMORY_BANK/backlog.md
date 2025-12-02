# Backlog & Future Ideas

These are **not active tasks**; they should be pulled into new playbooks when prioritized.

## Semantic / AI Search (Backlog)

- Compute embeddings for items (title + description + text_content).
- Add `/api/search/semantic` that returns similar items for a natural language query.
- Frontend “Semantic search” toggle in the grid.
- Could use:
  - Stub provider in tests/dev.
  - Real provider (e.g. OpenAI) in production later.

## Collections & Favorites

- Collections / boards, with many‑to‑many item membership.
- `is_favorite` flag (possibly per user).
- New filters for `collection_id` and `favorite=true` on `/api/items`.
- UI:
  - Collections list / sidebar.
  - Star/unstar actions on cards + detail.
- Already has a draft playbook concept; implement when ready.

## Collaboration & Sharing

- Multi‑user flows beyond single admin.
- Shared boards / collections.
- Public read‑only share links.

## QoL / UX Polish

- Batch operations (multi‑select for tagging/moving).
- Keyboard shortcuts.
- Better empty states and onboarding hints.
- Optional dark mode.
