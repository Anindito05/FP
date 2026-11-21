# Design

## Scope

An LLM-based wellness companion with independent safety routing, optional verified resource discovery, consent controls, encrypted conversation storage, and a lightweight React client. It is not therapy or a crisis line.

## Data model

`users`, rotating `refresh_tokens`, `chat_sessions`, encrypted `messages`, `message_analysis` (including model and prompt version JSON), `risk_events`, `consents`, `feedback`, `audit_logs`, `eval_runs`, and `help_search_cache`. Legacy KB tables and static helplines are removed in migration 0002. No RAG vectors are stored this semester.

## Safety

`ml/risk.py` normalizes Unicode, punctuation, repeated letters, slang variants, and scans deterministic patterns on every message. Structured analysis uses `analysis.v1.md`, Pydantic validation, JSON schema mode, low temperature, and one correction retry. Risk is the max/OR of model and keyword severity; ambiguous language is conservatively elevated by the prompt. Failure uses keyword-only plus recent escalation trend rather than routing all users to crisis. Any medium/high turn receives static copy marked `NEEDS HUMAN/CLINICAL REVIEW`, logs a `risk_events` row, and never calls the companion prompt. Normal replies run through `check_response`.

## LLM and prompts

The only model is configured by `LLM_MODEL` via Ollama Cloud. Versioned files in `app/prompts/` cover analysis, companion, helpline extraction, and nearby extraction. Templates are cached at first use. Analysis uses Ollama's JSON schema `format`; temperature is 0.1. The companion uses a conservative 400-token response budget and at most eight recent messages.

## Resource discovery

Ollama `/api/web_search` queries user-provided location; top results are optionally fetched through `/api/web_fetch`. Extraction receives delimited untrusted content. Each record must point to a page among retrieved sources. Every phone is normalized to digits and retained only if it appears in that source. Preferred domains are configurable. Results cache for `HELP_SEARCH_TTL_DAYS` (30 default). Empty/unverified searches show source links and advise contacting the local emergency number or a trusted person without inventing digits.

## Privacy and auth

Refresh tokens rotate and reuse revokes their family. Message body is encrypted with Fernet before persistence. No raw IP or message text is logged. Data logging and location lookup are separate consent records. Frontend keeps access token in memory and refresh token in sessionStorage (lost when tab session ends; accessible to same-origin script).

## Evaluation

`data/eval_risk.csv` is a tiny, hand-written synthetic smoke set. CLI reports keyword-only, LLM-only, and combined precision/recall/F2/FNR, category recall, and latency percentiles; analysis with an unavailable model yields degraded data and is not a meaningful LLM-only measurement. `POST /admin/eval` stores combined metrics in `eval_runs`. Phone extraction should be evaluated with fixed mocked web results and must report verified fraction. No result here is clinical evidence.

## Future RAG

`app/rag.py:get_context(query, db)` currently returns an empty list. See [rag-design.md](rag-design.md) for next-semester design.
