# Auth and local setup

## Setup

Python 3.11+, Node 20+, Neon PostgreSQL, Ollama Cloud key. Configure backend `.env` from `.env.example`; pooled `DATABASE_URL` serves the API and direct `DATABASE_URL_DIRECT` serves Alembic. Use asyncpg URLs with `?ssl=require`. The first migration drops legacy RAG/helpline tables and creates the verified-search cache.

### Windows PowerShell

```powershell
cd C:\Users\DELL\OneDrive\Documents\CODEX\FYP\FYP-G6-CS2
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env
alembic upgrade head
uvicorn app.main:create_app --factory --reload --port 8000
```

In a second terminal:

```powershell
cd C:\Users\DELL\OneDrive\Documents\CODEX\FYP\FYP-G6-CS2-FRONTEND
Copy-Item .env.example .env
npm install
npm run dev
```

### bash

```bash
cd FYP-G6-CS2
python3.11 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Edit .env
alembic upgrade head
uvicorn app.main:create_app --factory --reload --port 8000
```

Second terminal: `cd FYP-G6-CS2-FRONTEND && cp .env.example .env && npm install && npm run dev`.

## Environment variables

Backend variables and defaults are fully listed in `.env.example`: database URLs, JWT/encryption keys, access/refresh TTLs, `OLLAMA_HOST`, `OLLAMA_API_KEY`, `LLM_MODEL`, timeout, CORS, rate limit, retention, search cache TTL, result limit, and preferred domains. UI uses `VITE_API_BASE_URL` in its `.env.example`.

## Auth API

- `POST /api/v1/auth/register`: email, password, display name, accepted terms.
- `POST /api/v1/auth/login`: email and password.
- `POST /api/v1/auth/guest`: accepted terms.
- `POST /api/v1/auth/refresh`: rotates refresh token; reuse revokes its family.
- `POST /api/v1/auth/logout`, `GET/DELETE /api/v1/users/me`.

Access token stays in React memory. Refresh token uses `sessionStorage`, which survives reload within a tab session but is accessible to same-origin scripts. Message content is encrypted at rest. Never commit `.env` files.

Grant `data_logging` consent before sending chats. Grant `location_lookup` before nearby search; provide city/country directly. Helpline search is public, but the UI only exposes it through the optional escalation flow. Lookup results may be empty and any shown number must include its source and verification note.

Health: `/api/v1/health/live` and `/api/v1/health/ready`. Synthetic evaluation: `python scripts/run_eval.py`; pytest uses fakes where configured. Do not treat synthetic metrics as evidence of effectiveness.
