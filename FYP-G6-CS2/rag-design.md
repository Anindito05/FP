# RAG design

## This phase: classifier retrieval

`app/ml/rag_classifier.py` embeds each user message and a weighted short window of recent user turns. It searches emotion-class shards, votes with similarity-squared weights, applies minimum similarity and confidence/novelty reporting, and returns unknown when evidence is insufficient. Tier A verified examples may supply risk labels; Tier B verified examples supply emotions only when explicitly enabled. Tier C and unverified sources are rejected. See `docs/dataset-governance.md` for human data acquisition and auditing.

`app/ml/index_store.py` reads versioned float16 disk shards, centroids and an emotion-neighbour graph. Small classes load hot; large classes page from disk under an LRU RAM cap. Low confidence or rising level expands cold paging. Build with `python scripts/build_index.py --manifest data/datasets.yaml`; use `--synthetic` only for pipeline demos. Artifacts under `models_store/index/<version>` are ignored by git and must be copied to each deployment host. `INDEX_VERSION` selects the loaded version without code changes.

The current hashing embedder makes tiny deterministic local fixtures possible without downloads. Configure `EMBED_MODEL` to a small English sentence-transformers MiniLM model for research use (Python 3.11+). Rebuild the entire index whenever the embed model changes.

## Next semester: wellness knowledge

Reuse the embedder interface and shard file format for reviewed, non-personal public coping/information material. Keep a separate index namespace and governance manifest from classifier examples. Implement only `app/rag.py:get_context(query, db)` to retrieve approved chunks with publisher/source metadata. Then extend `build_messages` to attach relevant chunks and validated citations. Never retrieve private conversation data or let knowledge retrieval influence safety routing. The seam currently returns an empty list.

## Evaluation limits

The synthetic fixture verifies plumbing only. Real evaluations require permissioned datasets, held-out user/thread splits, per-tier reporting, calibration and clinical review; report “retrieval over clinician-annotated examples”, never “clinically validated classifier”.
