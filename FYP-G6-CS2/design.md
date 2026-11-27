# Design

## Classification and safety

Each message is embedded locally with recent user turns as context and matched against governed labeled examples. Similarity-weighted emotion and level distributions include confidence and novelty; low similarity yields unknown. Risk routing is restricted to Tier A verified examples. The keyword net always runs and can only raise the result. The mood tracker smooths emotion, records gradual/abrupt shifts, raises quickly, and lowers with hysteresis. Level 4 is scripted and never calls the companion. Levels 2–3 adjust Alex's prompt; level 3 carries an optional offer.

The V2 analysis prompt stays in `app/ml/legacy_analysis.py` only for offline ablations. Runtime has one LLM reply call for ordinary chat. Missing index means degraded mode using keyword plus trend, with conservative Alex tone.

## Alex

`companion.v2.md` and non-removable `guard.v1.md` specify short, natural, honest replies. Output checks reject identity/credential/contact/confidentiality claims, medication/method advice, lists and stock AI boilerplate. “Are you human/bot/AI?” receives a guaranteed truthful response. Crisis copy remains marked for clinical review.

## Storage and operations

Encrypted messages remain the source for user-visible history. `message_analysis` stores only labels, score distributions, dataset item IDs, versions and classifier metadata. `mood_states` stores one compact label-only snapshot per user turn. Index files are versioned, float16 shards on disk with bounded paging/LRU and a small hot tier. Neon contains dataset and index metadata only. `get_context()` remains empty for next semester's reviewed wellness-knowledge RAG.

Admin reviewers see risk events, label-only mood timelines, and system metrics. This semester's shipped fixture is synthetic and is excluded from reported real-data performance claims.
