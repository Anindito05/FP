# Build and run

## Backend prerequisites

Python 3.11+, PostgreSQL/Neon, an Ollama Cloud API key. Set `DATABASE_URL` to Neon pooled asyncpg URL and `DATABASE_URL_DIRECT` to direct URL; both use `?ssl=require`. Provide strong `JWT_SECRET`, Fernet `FIELD_ENCRYPTION_KEY`, `OLLAMA_API_KEY`, and verify the Gemma 4 model tag before use.

### Windows PowerShell

```powershell
cd C:\Users\DELL\OneDrive\Documents\CODEX\FYP\FYP-G6-CS2
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env with Neon credentials and generated keys
alembic upgrade head
uvicorn app.main:create_app --factory --reload --port 8000
```

### bash

```bash
cd FYP-G6-CS2
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Edit .env with Neon credentials and generated keys
alembic upgrade head
uvicorn app.main:create_app --factory --reload --port 8000
```

## Frontend

Create `frontend/.env` (or `FYP-G6-CS2-FRONTEND/.env`) from `.env.example`, set `VITE_API_BASE_URL=http://localhost:8000/api/v1`, install Node 20+ dependencies with `npm install`, and run `npm run dev`. Run `npm run build` and `npm run lint` before review.

## Safety and data checks

The crisis text is marked for human/clinical review. Use only synthetic examples locally; do not enter real crisis disclosures in tests. `scripts/run_eval.py` prints ablations on a tiny synthetic set; it is not clinical evidence. Use fake LLM and web clients for automated tests. Before pilot: clinical review, verify model tag, hand-check resource results, and ethics review.

## Local Ollama gateway (no Cloud key required)

The backend calls the local gateway on port 8001; the gateway forwards requests to the Ollama daemon on port 11434. On the model host, install/start Ollama and pull the chosen model:

```powershell
ollama pull gemma3:270m
```

Start three terminals from the backend folder:

```powershell
# Terminal 1: gateway on 127.0.0.1:8001
uvicorn app.llm_gateway:app --host 127.0.0.1 --port 8001
```

```powershell
# Terminal 2: backend
uvicorn app.main:create_app --factory --reload --reload-dir app --reload-dir migrations --port 8000
```

```powershell
# Terminal 3: frontend (from FYP-G6-CS2-FRONTEND)
npm run dev
```

Check `http://127.0.0.1:8001/health` before chatting. Set `OLLAMA_LOCAL_URL` if the Ollama daemon runs on a different host. For deployment, host the gateway beside Ollama and set the backend's `OLLAMA_HOST` to the gateway's reachable private URL; do not expose the unauthenticated gateway directly to the public internet. A gateway does not supply model compute itself; the deployment still needs a running Ollama daemon and the model pulled there.
