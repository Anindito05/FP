# Architecture

College-scale support companion: React/Vite → FastAPI → SQLAlchemy async → Neon PostgreSQL, with Ollama Cloud Gemma for structured analysis, companion replies, and web-result extraction.

```text
React UI (memory access token; sessionStorage refresh token)
  └─ FastAPI routers → services → encrypted message store / consent / risk events
       ├─ risk.py deterministic normalized keyword net (always runs)
       ├─ nlu.py analysis.v1 structured Ollama call; keyword OR analysis gates crisis
       ├─ safety.py reviewed-needed static crisis text and output filter
       ├─ rag.py get_context() → [] (next-semester insertion point)
       ├─ prompts/*.v1.md loaded once and version-recorded
       └─ help_search_service: Ollama search/fetch → extraction → digit verification
```

## Request flow

1. Authenticated chat checks data-logging consent, ownership, and idempotency; user text is encrypted before commit.
2. A structured analysis call and deterministic keyword scan run concurrently. Medium/high from either signal routes to the scripted crisis path. Failed analysis falls back to keyword results and escalation trend, sets `keyword_fallback`, and uses a gentle-check-in prompt on ordinary turns.
3. Only ordinary turns call the companion LLM. Recent history is included within a small fixed turn budget. Rule-based `check_response` runs on every generated reply.
4. Prompt and model versions are recorded on `message_analysis`; message contents never enter application logs.
5. Crisis flow presents an optional offer. Location search requires explicit `location_lookup` consent and user-entered country/city. Extracted phone digits must occur in fetched source text; returned results carry source URLs and a verification note.

## Persistence and operations

Neon pooled URL is for the app; direct URL is for Alembic. Both asyncpg URLs use `?ssl=require`. Migrations drop legacy `kb_sources`, `kb_chunks`, vector extension, and CSV-backed `helplines`; they add `prompt_versions` and TTL cache `help_search_cache`. No pgvector, model weights, or embeddings are used.

Run backend from `FYP-G6-CS2`: `uvicorn app.main:create_app --factory --reload --port 8000`. Run UI from sibling `FYP-G6-CS2-FRONTEND`: `npm run dev`. See [auth.md](auth.md) for PowerShell and bash setup.

## Known limits

Risk prompts and scripts are not clinically validated. Web results can be incomplete or wrong even when a phone number is present; verify sources manually. The cache key uses location terms, not user identity. The UI and admin functions are college-scale and require security, accessibility, and real-user ethics review before any pilot.
