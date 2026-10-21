# Trace — Agentic RAG with Trust Scoring

A retrieval-augmented generation system built around one question: **not just "what's the answer," but "how much should you trust it, and why?"**

Three agents (retriever, generator, critic) collaborate on every query, a trust score is computed from source authority/agreement/recency and shown to the user with its reasoning, and the whole system runs as a concurrent multi-user FastAPI service with isolated per-session state.

This project was built to extend an existing production RAG system with three specific research directions, each mapped to a real limitation of naive RAG:

| Direction | What it addresses | Research fit |
|---|---|---|
| **Trust scoring & provenance** | LLMs generate fluent answers regardless of whether sources actually support them | Trust and privacy, multi-agent systems |
| **Scalable multi-agent coordination** | Most RAG demos are single-user scripts, not systems that hold up under concurrent load | Multi-agent systems, scalability & dependability of distributed systems |
| **Uncertainty-aware responses** | A model that always sounds confident is worse than one that says "I'm not sure" when it should | Reasoning under uncertainty |

## Live demo

```bash
pip install -r requirements.txt

# Optional: use a real LLM instead of the deterministic mock
export ANTHROPIC_API_KEY=your_key_here

cd src
uvicorn api:app --reload --port 8420
```

Then open `http://localhost:8420` — a chat interface where every answer shows its trust score breakdown, sources, and the critic agent's raw critique inline.

**To demonstrate concurrent multi-user handling live:** open two browser tabs side by side, ask different questions in each at the same time, and watch both resolve independently with separate session IDs and no cross-talk in conversation history.

Without `ANTHROPIC_API_KEY` set, the system runs against a deterministic mock LLM — the full pipeline (retrieval, trust scoring, session isolation, concurrency) is real and testable either way; only the generated text itself is mocked.

## Architecture

```
User query
    │
    ▼
┌─────────────────┐
│  Retriever Agent │  TF-IDF + cosine similarity over document corpus
└────────┬─────────┘
         │ retrieved chunks
         ▼
┌─────────────────┐      ┌──────────────────┐
│ Generator Agent  │ ───▶ │   Critic Agent    │  checks draft against
│  drafts answer   │      │  flags unsupported │  sources, flags disagreement
└─────────────────┘      │  claims/disagreement│
         │                └──────────────────┘
         ▼
┌─────────────────────────────────────────┐
│           Trust Scorer                    │
│  authority (0.5) + agreement (0.35)        │
│  + recency (0.15) → overall trust score    │
└─────────────────────────────────────────┘
         │
         ▼
   Response + trust breakdown + low-trust warning if applicable
```

All of this runs inside a FastAPI backend where each request is an independent async task, with a `SessionManager` keeping per-user conversation history isolated via per-session locks (see `src/session_manager.py`).

## Concurrency results

`tests/test_concurrent_users.py` simulates four simultaneous users querying the system at once and measures actual wall-clock behavior:

```
4 concurrent users, total wall time: 1.216s
Sum of individual request times: 4.818s
Concurrency speedup: 3.96x

Session isolation check:
  Alice   : history=['how do I save money on S3 storage'] OK
  Bob     : history=['what are Lambda concurrency limits'] OK
  Carol   : history=['how does DynamoDB capacity mode work'] OK
  Dave    : history=['how do I save money on S3 storage'] OK

All checks passed: concurrent requests succeeded with isolated sessions.
```

Four users complete in roughly the time one would take serialized, and no session ever sees another user's query — the two properties that matter for a genuinely multi-user system rather than a single-user demo wearing a web server.

## Trust calibration: an honest evaluation, including where it breaks

`evaluate.py` runs a small labeled set of queries — some expected to retrieve clean, high-authority sources, some deliberately chosen because they're likely to pull in a low-authority forum/blog post already seeded in the corpus — and checks whether the trust score correctly separates them.

```
Query                                          Trust  Expected Low?  Actual Low? Match
-----------------------------------------------------------------------------------------------
AWS S3 lifecycle transition rules              0.503          False         True ✗ MISS
AWS DynamoDB read write capacity               0.592          False        False ✓
S3 Intelligent-Tiering archive tier            0.509          False         True ✗ MISS
how do I save money on S3 storage              0.503           True         True ✓
Lambda cold start performance tips              0.380           True         True ✓
-----------------------------------------------------------------------------------------------
Trust calibration accuracy: 3/5 (60%)
```

**This is not a bug I hid — it's the most interesting finding in the project.** Digging into the two misses: both queries retrieved a low-authority document purely on lexical overlap (TF-IDF matched keywords like "Glacier" or "tiering" in the forum post even though it wasn't the best source), which correctly triggered a low-trust flag — but for reasons that weren't really about factual disagreement, just retrieval imprecision.

**The finding:** trust scoring is only as good as retrieval precision. A trust layer built on top of imprecise retrieval will sometimes flag correct, well-supported answers as low-trust simply because a marginal, low-quality document got pulled into the top-k. This points directly at future work: swapping TF-IDF for dense embeddings, or adding a minimum-similarity cutoff before documents are eligible for trust scoring at all, would likely close most of this gap. I'd rather report a real 60% with a clear explanation than a suspicious 100% on a five-query toy eval.

## Project structure

```
agentic-rag-trust/
├── README.md
├── requirements.txt
├── evaluate.py                    # trust calibration evaluation
├── data/
│   └── corpus.json                # sample document corpus (mixed authority)
├── src/
│   ├── vector_store.py            # TF-IDF retrieval
│   ├── trust_scorer.py            # authority/agreement/recency scoring
│   ├── agents.py                  # retriever/generator/critic orchestration
│   ├── llm_provider.py            # pluggable real (Anthropic) / mock LLM
│   ├── session_manager.py         # per-user concurrency-safe session state
│   └── api.py                     # FastAPI backend
├── web/
│   └── index.html                 # demo chat UI with visible trust breakdown
└── tests/
    └── test_concurrent_users.py   # concurrency + session isolation test
```

## Why these design choices

- **TF-IDF over embeddings for retrieval:** kept the system dependency-light and fully offline-runnable (no model downloads), at the honest cost of retrieval precision documented above. A clear, known trade-off rather than an oversight.
- **Pluggable LLM provider:** the agent orchestration, trust scoring, and concurrency logic are all testable and demoable without API cost or key setup, and swap to a real Anthropic model with one environment variable.
- **In-memory session store:** appropriate for a portfolio-scale demo; the `SessionManager` interface is written so swapping in Redis for real multi-process deployment is a single class change, not a rewrite.
- **Critic agent as a genuine second opinion, not a rubber stamp:** the system is explicitly instructed to be skeptical, and the trust score is computed independently of whether the critic approves — so a fluent, critic-approved answer can still carry a low trust score if its underlying sources are weak.
