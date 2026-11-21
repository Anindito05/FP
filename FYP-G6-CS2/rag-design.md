# Next-semester RAG design

## Goals and boundaries

Ground ordinary factual wellness answers in a small, reviewed public corpus. Do not retrieve personal records, user conversations, crisis scripts, or unreviewed web pages. RAG must never override risk routing or be called for a flagged turn.

## Corpus and sources

Use public, non-personal materials from WHO, NIMH, and university counseling or student-wellbeing pages. Keep publisher, title, canonical URL, retrieval date, license/terms, checksum, and review status. Review permissions and freshness before ingestion. Exclude forums, comments, and identifiable stories.

## Chunking and embeddings

Preserve headings and source boundaries; begin with 350–500 token chunks and 50–80 token overlap, then compare retrieval quality. Choose a maintained multilingual sentence embedding model that fits deployment and document version, dimensionality, and license. Benchmark against lexical search before selecting it. Do not commit model weights.

## PostgreSQL design

After enabling pgvector by migration, add `kb_sources` (metadata and active/reviewed status) and `kb_chunks` (source FK, chunk index, plain public text, token count, embedding vector, heading metadata). Use HNSW with cosine distance after measuring Neon support and dataset size. Keep migrations reversible and test against a disposable Neon branch.

## Plug-in point and citations

Implement only `app/rag.py:get_context(query, db) -> list[ContextChunk]`. `chat_service` already calls it and passes chunks into prompt building. Return source metadata with each chunk. Companion answers should cite stable source IDs/URLs in a constrained format; validate that citations point to retrieved sources, render links in the UI, and avoid claiming a statement is sourced when no matching chunk is present.

## Evaluation

Create reviewed question/answer pairs with expected source IDs, measure recall@k, MRR, citation precision, answer groundedness, and abstention quality. Blindly compare the current prompted analysis with a fine-tuned classifier on a separate, consented, de-identified, clinically reviewed dataset; report calibration, per-category recall, F2, FNR, latency, and uncertainty. Synthetic data is only a pipeline check.

## Helpline directory evolution

Current web search is a fallback discovery path and verifies phone digits against fetched text. Replace it over time with a curated, reviewed, versioned directory (country/region, service, eligibility, hours, phone, source and verification date). Keep search as a fallback when no current directory entry exists; never let either a model or an embedding infer a number.
