# BRAIN Inspiration Vault

BRAIN is a self-hosted inspiration vault designed to help you collect, organize, and retrieve ideas. It serves as a private "second brain" for saving generic URLs, social media posts (Tweets, Pins), and local files (images, PDFs), all accessible via a visual grid interface.

## 🧠 Project Overview

The core philosophy of BRAIN is to provide a frictionless way to capture content and a powerful way to retrieve it later, all while keeping your data private and self-hosted.

### Key Features (v1)

-   **Link Saving:** Save generic URLs with automatic metadata extraction (Title, Description, OpenGraph images).
-   **Social Media Integration:** specialized handling for Twitter/X and Pinterest (saving text, authors, and images).
-   **File Uploads:** Upload local images and PDFs.
-   **Visual Grid:** Browse all your content in a responsive, masonry-style grid.
-   **Search & Filter:** Full-text search across titles, descriptions, and extracted text (PDFs), with filters for content type.
-   **Private:** Designed to run behind a reverse proxy with authentication.

## 🏗 Architecture

BRAIN follows a modern full-stack architecture:

-   **Frontend:** React (Vite) SPA.
-   **Backend:** FastAPI (Python) application using SQLAlchemy for ORM.
-   **Database:** PostgreSQL.
-   **Storage:** Designed to work with networked storage (e.g., Unraid NFS share) or local storage.

## 🚀 Getting Started (Local Development)

### Prerequisites

-   Docker & Docker Compose
-   Node.js & npm (for frontend development)
-   Python 3.12+ (for local backend development without Docker)

### Quick Start with Docker

The easiest way to run the entire stack is using Docker Compose.

1.  **Navigate to the deploy directory:**
    ```bash
    cd deploy
    ```

2.  **Start the services:**
    ```bash
    docker-compose up --build
    ```

    This will start:
    -   **Backend:** http://localhost:4000 (Health check: `/health`)
    -   **Database:** PostgreSQL on port 5432

3.  **Run the Frontend (Separate Terminal):**
    For a better developer experience (HMR), run the frontend locally.
    
    ```bash
    cd frontend
    npm install
    npm run dev
    ```
    Access the UI at http://localhost:5173

### Configuration

Environment variables are managed via `.env` files. 
-   **Backend:** See `backend/core/config.py` or `deploy/docker-compose.yml` for defaults.
-   **Frontend:** Vite environment variables (prefixed with `VITE_`).

## 📂 Project Structure

```
APP_/
├── backend/        # FastAPI application source code
│   ├── app/        # Main app logic (models, schemas, api routes)
│   └── ...
├── frontend/       # React application source code
├── deploy/         # Docker Compose and deployment configuration
└── storage/        # Local mount point for file storage (ignored in git)
```

## 🔍 Search & Filtering API

The frontend grid consumes `GET /api/items`, which always returns the newest items first and exposes several query parameters that can be combined:

| Parameter | Description |
| --- | --- |
| `q` | Case-insensitive keyword search across `title`, `description`, and extracted `text_content`. |
| `type` | Restrict results to a specific `ItemType` (`url`, `image`, `pdf`, etc.). |
| `tag` | Filter by a single tag name. |
| `tags` | Provide multiple `tags=foo&tags=bar` values to require **all** of the tags (intersection semantics). |
| `created_from` / `created_to` | ISO-8601 timestamps (UTC). Limit results to a date range. |
| `limit` / `offset` | Standard pagination; defaults to `limit=50` newest items, `offset=0`. |

Example requests:

```http
GET /api/items?q=moodboard
GET /api/items?type=image&tag=poster
GET /api/items?created_from=2025-01-01T00:00:00Z&created_to=2025-01-31T23:59:59Z
GET /api/items?q=nostalgia&type=pdf&tags=article&tags=reference&limit=10&offset=20
```

`ItemOut` includes the fields a grid view can rely on: `id`, `type`, `title`, `description`, `origin_domain`, `thumbnail_path`, `file_path`, `tags[]`, `created_at`, and `updated_at`. Tag assignments are managed via:

- `PUT /api/items/{item_id}/tags` — replace an item's tags with the provided list (idempotent).
- `GET /api/items/{item_id}/tags` — fetch the tags currently attached to an item.
- `/api/tags` — create/list/delete tags with per-user uniqueness.

## 🛠 Deployment

In production (e.g., a VPS), the `storage` directory is expected to be a mount point (e.g., via NFS from a NAS) where all binary assets are stored.

See `deploy/docker-compose.yml` for the production-ready service definitions.

---
*v1.0.0*