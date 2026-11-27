# Architecture

## Runtime

React/Vite/TypeScript client → FastAPI async API → SQLAlchemy 2 async/asyncpg → Neon PostgreSQL. Messages remain encrypted at rest. Classification uses a local embedder, a versioned disk shard index with bounded LRU page cache, RAG weighted-neighbour voting, a per-session mood tracker, and an always-on deterministic keyword net. The model is loaded once in FastAPI lifespan. Ollama Cloud Gemma 4 is called once for ordinary replies; level 4 uses a scripted response and never calls the companion. Verified helpline/web search stays unchanged.

```text
chat turn → keyword net + local classifier → mood/level fusion → level 4 scripted crisis
                                                        └→ Alex prompt + guard → one reply call
future wellness RAG → app/rag.py:get_context() → reviewed public knowledge only
```

## Data and operations

Dataset policy lives in `data/datasets.yaml`; no real or restricted dataset ships. `scripts/build_index.py` refuses unverified/Tier C sources and ignores Tier B unless explicitly enabled. Index artifacts go to ignored `models_store/index/<version>` and must be copied with the same version to deployment hosts. Neon stores audit metadata and compact mood snapshots, never embeddings or raw classifier inputs. `/health/ready` reports classifier mode, index, tiers and cache stats.

Migrations 0001–0002 preserve auth, encrypted chat, risk review and verified help search; 0003 adds dataset/index manifests, message analysis fields and mood states. Migrations use the direct URL, API uses pooled `DATABASE_URL`.

## Boundaries and limits

This is a supportive companion, not therapy, diagnosis, or a clinical tool. The synthetic hashing embedder is only for local engineering demos; use configured sentence-transformers MiniLM on Python 3.11+ for semantic evaluation. No dataset candidate is verified or enabled by default. The severity mapping and crisis language need clinical review. `get_context()` remains reserved for next-semester wellness knowledge; classifier examples are not prompt context.
