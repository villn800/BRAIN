# BRAIN Repo Export Summary

## 0. Meta
- **Scan Date:** Saturday, December 13, 2025
- **Scanned Path:** `/Users/robot1/Downloads/CURSOR_/BRAIN_`
- **Total Size:** 481M
- **File Count:** 14,551
- **Directory Count:** 1,769

## 1. High-level Purpose + Architecture (Inferred)
- **Type:** Full-stack Web Application (Python Backend + React Frontend)
- **Structure:** Monorepo-style with `APP_` containing `backend` and `frontend`.
- **Backend:** Python (FastAPI/Flask likely), utilizing `alembic` for migrations, `pydantic` for validation, and `playwright` for automation/scraping.
- **Frontend:** React-based (Vite build tool), using `esbuild`.
- **Entry Points:**
  - Backend: `APP_/backend/app/main.py` (likely)
  - Frontend: `APP_/frontend/index.html`
- **Config:** `docker-compose.yml` for orchestration, `requirements.txt` for Python, `package.json` for Node.

## 2. Disk Usage Hotspots

### 2.1 Largest Directories (Top 20)
| Directory | Size | Notes |
| :--- | :--- | :--- |
| `/APP_/backend/.venv` | 260M | **Duplicate Venv?** (Larger than root venv) |
| `/.venv` | 138M | **Duplicate Venv?** (Root level) |
| `/APP_/frontend/node_modules` | 47M | Standard frontend dependencies |
| `/APP_/.git` | 8.4M | Version control history |
| `/APP_/SCRIPTS_` | 3.6M | Contains large data files |
| `/APP_/backend/manual_manual.db` | 1.8M | SQLite Database (local dev?) |
| `/DOCS_` | 392K | Documentation |
| `/APP_/frontend/dist` | 232K | Frontend build artifacts |

### 2.2 Largest Files (Top Examples)
| File | Size | Type | Likely Purpose | Trim Option |
| :--- | :--- | :--- | :--- | :--- |
| `APP_/backend/.venv/.../playwright/driver/node` | 111M | Binary | Playwright Browser Driver | Keep (Required dependency) |
| `.../cryptography/.../_rust.abi3.so` | 21M | Binary | Crypto Lib (Duplicated in both venvs) | Consolidate Venvs |
| `APP_/deepseek_results.log` | **20M** | Log | Application Logs | **IGNORE / DELETE** |
| `.../esbuild/.../bin/esbuild` | ~10M | Binary | Frontend Build Tool | Keep (Dev dep) |
| `APP_/SCRIPTS_/liked_tweets.json` | 3.7M | JSON | Data Dump | Git LFS or Ignore |
| `APP_/backend/manual_manual.db` | 1.8M | SQLite | Local Dev DB | **IGNORE** |

## 3. File-Type Breakdown
| Extension | Count | Approx Notes |
| :--- | :--- | :--- |
| `.pyc` | 4,967 | Python Bytecode (Generated) |
| `.py` | 4,853 | Python Source |
| `.js` | 1,739 | JavaScript (Source + Deps) |
| `.map` | 430 | Source Maps (Debug) |
| `.md` | 134 | Markdown Docs |
| `.ts` | 132 | TypeScript |
| `.txt` | 127 | Text / Config |
| `.json` | 101 | Config / Data |
| `.so` / `.dylib` | ~110 | Native Libs (Heavy) |

## 4. Duplicate Candidates
- **Virtual Environments:** Two separate `.venv` directories exist (`/.venv` and `/APP_/backend/.venv`). They share many heavy libraries (`cryptography`, `PIL`, `psycopg2`), accounting for ~150MB+ of redundancy.
- **Dependencies:** `esbuild` binaries likely exist in multiple distinct node sub-dependencies or versions if not deduplicated by npm/yarn.

## 5. Generated / Cache / Vendor Findings
| Path | Size | Recommendation |
| :--- | :--- | :--- |
| `/APP_/backend/.venv` | 260M | **CRITICAL:** Decide on one venv. The backend one seems more complete (has Playwright). |
| `/.venv` | 138M | **CRITICAL:** Remove if redundant to the backend one. |
| `/APP_/frontend/node_modules` | 47M | Keep locally, ensure in `.gitignore`. |
| `__pycache__` (cumulative) | ~1M | Safe to delete, will regenerate. |
| `dist/` | ~230K | Build artifact, ensure in `.gitignore`. |

## 6. Trim Plan (Actionable)

### Quick Wins (Immediate Space Recovery)
- **Delete `APP_/deepseek_results.log`** (Save 20MB).
- **Consolidate Virtual Environments:**
  - If `APP_/backend/.venv` is the primary one used by the app, delete the root `/.venv`.
  - **Potential Savings:** ~138MB.
- **Clean `__pycache__`:**
  - Run `find . -name "__pycache__" -type d -exec rm -rf {} +`.

### Medium Effort
- **Data Management:**
  - `APP_/SCRIPTS_/liked_tweets.json` (3.7MB) and `APP_/backend/manual_manual.db` (1.8MB) should likely be git-ignored and not tracked in the repo.
- **Documentation:**
  - `/DOCS_` is small (392K), but ensure no large binary assets (images/videos) are added there in the future.

### Risky / Confirm First
- **Playwright:** The 111MB driver is massive. If this is a production deployment that doesn't need the browser driver (e.g. headless scraping handled elsewhere), `playwright` could be moved to a separate dev-only requirement or installed dynamically.

## 7. Suggested .gitignore Additions
```gitignore
# Logs
*.log
deepseek_results.log

# Database
*.db
*.sqlite3
manual_manual.db

# Virtual Environments (Ensure all variations are caught)
.venv/
venv/
env/

# Data Dumps
liked_tweets.json

# Build Artifacts
dist/
build/
__pycache__/
```

## 8. Notes
- The repo is relatively clean aside from the **double virtual environment** issue and the large **log file**.
- **Secret Scan:** No obvious keys in filenames, but `deepseek_results.log` should be checked to ensure it didn't log API keys or sensitive scraped data before deletion.
