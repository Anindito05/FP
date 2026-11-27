# Phase 3 build steps

1. Read architecture/design/auth/rag docs and inspect existing APIs.
2. Keep the deterministic keyword scan first-class; add level taxonomy and governance-gated local classifier retrieval.
3. Build versioned local shards only from verified manifest entries or explicit synthetic fixture mode.
4. Persist mood labels/scores only and route level 4 to the scripted crisis handler before any companion call.
5. Use Alex prompt plus honesty guard for normal replies; keep V2 analysis prompt exclusively as an offline baseline.
6. Update admin and client contracts, then run backend/fake tests and frontend build/lint.
7. Add governed datasets only after human verification; synthetic metrics are never effectiveness claims.

## Current implementation notes

`python scripts/build_index.py --synthetic --version demo` builds the example index. Normal startup without a built index is degraded but functional. The Python 3.11+ deployment setup is documented in `steps.md`; the checked-in dev virtual environment may not match it.
