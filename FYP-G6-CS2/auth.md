# Auth and local setup

## Setup

Python 3.11+, Node 20+, Neon PostgreSQL and Ollama Cloud. `.env.example` lists API, auth, embedding, index paging, threshold, and mood settings. Use pooled `DATABASE_URL` for the API and direct `DATABASE_URL_DIRECT` for migrations. Keep credentials and private corpora out of git.

## Windows PowerShell

```powershell
cd C:\Users\DELL\OneDrive\Documents\CODEX\FYP\FYP-G6-CS2
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Set database credentials, secrets, Ollama settings
alembic upgrade head
python scripts/build_index.py --synthetic --version demo
$env:INDEX_VERSION = "demo"
uvicorn app.main:create_app --factory --reload --port 8000
```

Second terminal:

```powershell
cd C:\Users\DELL\OneDrive\Documents\CODEX\FYP\FYP-G6-CS2-FRONTEND
Copy-Item .env.example .env
npm install
npm run dev
```

## bash

```bash
cd FYP-G6-CS2
python3.11 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Set database credentials, secrets and Ollama settings
alembic upgrade head
python scripts/build_index.py --synthetic --version demo
INDEX_VERSION=demo uvicorn app.main:create_app --factory --reload --port 8000
```

Frontend second terminal: `cd FYP-G6-CS2-FRONTEND && cp .env.example .env && npm install && npm run dev`.

## Environment variables

Existing variables cover auth, database, Ollama, CORS, retention, and help search. Phase 3 variables: `EMBED_MODEL` selects local embedding model (`hashing-n-gram-v1` is only a dependency-free demo); `INDEX_VERSION` and `INDEX_DIR` select on-disk index; `ALLOW_PEER_REVIEWED_NON_CLINICAL` defaults false; `RAM_BUDGET_MB`, `PAGE_SIZE`, `TOP_K`, and `MIN_SIMILARITY` control index search; `LEVEL_HIGH_THRESHOLD`, `LEVEL_CRITICAL_THRESHOLD`, `LEVEL_CONFIDENCE_THRESHOLD`, and `LEVEL_DECAY` configure calibrated level policy; `HYSTERESIS_TURNS`, `PREFETCH_NEIGHBOURS`, and `MOOD_SMOOTHING` set mood behavior. Tune thresholds only from an authorized held-out calibration split.

Index artifacts under `models_store/index/<version>` are git-ignored and must be securely copied to deployment hosts. Never store user text or embeddings in index/log/audit tables. `/api/v1/health/ready` reports classifier mode, index, tiers, and cache/RAM metrics.

## Auth, consent, resources

Auth endpoints and consent requirements remain as before. Grant `data_logging` before chat and `location_lookup` before nearby search. Resource results retain source links and verification notes. Alex is an AI companion, not therapy or a crisis line.

## Human gates

Obtain and verify Tier A datasets and complete `TODO_VERIFY` in the registry. Have a clinician review levels, mappings and crisis wording. Confirm the actual Gemma 4 tag, manually check some helpline results, and receive ethics approval before any real-user pilot. See `docs/dataset-governance.md`.
