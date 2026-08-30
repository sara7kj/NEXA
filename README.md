# NEXA — Bilingual Enterprise Operations Agent

An Arabic/English retrieval and operations system for enterprise documents and
project data. An employee asks in Arabic; the system finds the answer in an
English policy document. A manager asks to change a project's status; the system
**refuses to execute it** until a director approves.

**Status:** Retrieval, authentication, tool layer, and the human-in-the-loop
approval flow are built, measured, and tested. The LangGraph agent that
orchestrates the tools is specified in `docs/` and not yet built.

All data in this repository is synthetic. No real company, person, or policy
is used.

---

## What this project is actually about

Putting an LLM in front of a database is easy. Doing it without creating a
system that can read rows it shouldn't, or execute changes nobody authorised,
is the hard part.

NEXA is built around one principle:

> **A prompt is a request. Code is a guarantee.**

Nothing in this system depends on the model behaving well. Permissions are
checked in the tool execution layer, identity comes only from a validated
token, and no sensitive action can run without a persisted human approval —
regardless of what any prompt, document, or model output says.

---

## Measured retrieval result

Evaluation set: 12 documents (6 EN, 6 AR), each topic in one language only.
24 questions, all strictly cross-lingual — the correct answer is never in the
same language as the question.

| Pipeline | Recall@1 | Recall@5 | Same-language bias |
|---|---|---|---|
| Dense retrieval only | 0.38 | 0.92 | 0.62 |
| Dense + cross-encoder rerank | **0.92** | — | **0.08** |

Same-language bias measures how often the top result shares the query's
language. 0.50 is neutral. Dense retrieval alone sat at 0.62 and capped
Recall@1 at 0.38. Reranking dropped the bias to 0.08 and lifted Recall@1
to 0.92.

Recall@5 of 0.92 under dense retrieval shows the correct document was almost
always *retrieved*. The failure was in **ranking**.

Full method, corrections, and limitations: [`docs/adr/ADR-009-embeddings.md`](docs/adr/ADR-009-embeddings.md)

---

## Security model

### No generated SQL — structurally, not by filtering

`query_projects` accepts only enum-typed filters. There is no `sql`, `where`,
or `filter_expression` field anywhere in any tool schema. An injection attempt
is not blocked by a check; it is rejected because **no field exists to carry it**.

### Identity is never taken from the model

`UserContext` is built once, from a validated JWT, and passed down as an
argument. It is never read from message text, model output, tool arguments,
conversation history, or retrieved document content. A tool call carrying
`{"user_role": "director"}` is rejected by the strict schema.

### No one is exempt from approval

| Actor | `update_project_status` |
|---|---|
| Employee | `PERMISSION_DENIED` |
| Manager | `APPROVAL_REQUIRED` |
| **Director** | `APPROVAL_REQUIRED` |
| With approval record | executes |

Approval is required by the tool's **static sensitivity classification**, not
by who is asking. There is no privileged role that bypasses the gate, and no
configuration flag that disables it.

### Approval invariants

- A request creates a pending record and **mutates nothing**.
- Execution uses the arguments **frozen at request time** — the model is never
  consulted again, so the human approves exactly what runs.
- A requester cannot approve their own request. Enforced in application code
  **and** as a database `CHECK` constraint.
- Execution re-verifies the target's current state; if it changed since the
  request, execution is blocked (`STATE_CHANGED_SINCE_REQUEST`).
- An approval executes at most once. Concurrent decisions serialise via
  `SELECT ... FOR UPDATE`.
- The audit record is written in the **same transaction** as the state change.
  A change without its audit row is not possible.

Every one of these is covered by a test.

---

## Audit trail

Who asked, who approved, on whose behalf, what changed, and when — in one
place. Denied attempts are logged too, because an auditor cares about who
*tried* as much as who succeeded.

`actor_role` is stored denormalised: promoting a user later must not rewrite
what the log says about their past actions.

---

## Architecture

Dependencies point downward only. The tool layer never imports API code; the
data layer knows nothing about roles.

Key decisions with rationale and rejected alternatives:
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

---

## Two corrections made during evaluation

Documented rather than quietly fixed, because how a result was reached matters
as much as the result.

**1. An early improvement was overfitting.** Per-language mean centering
appeared to lift Recall@1 from 0.50 to 0.80. On a held-out split the same
technique scored 0.08. It was rejected.

**2. The evaluation harness itself was wrong.** A dataset that paired every
topic with a translated twin required the model to pick the *foreign-language*
twin. When an English query was answered from an English document, the harness
scored it wrong — though that is correct behaviour. A reported Recall@1 of 0.00
was measuring a broken metric, not a broken system. Inspecting raw reranker
scores exposed it; aggregate numbers did not.

---

## Stack

Python 3.12 · FastAPI · PostgreSQL 17 · SQLAlchemy 2.0 · JWT + Argon2 ·
`intfloat/multilingual-e5-large` (retrieval) · `BAAI/bge-reranker-v2-m3` (rerank)

---

## Running locally

Requires Python 3.12 and PostgreSQL 17.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e .

createdb -U postgres nexa
cp .env.example .env            # set DATABASE_URL and JWT_SECRET

python -c "from nexa.db.connection import engine; from nexa.db.models import Base; Base.metadata.create_all(engine)"
python src/nexa/rag/ingest.py
python src/nexa/db/seed_users.py
python src/nexa/db/seed_projects.py

uvicorn nexa.api.main:app --reload
```

Open http://127.0.0.1:8000/docs

Dev accounts (password `dev-password-123`):
`layla@falcon.example` (employee) · `omar@falcon.example` (manager) ·
`huda@falcon.example` (director)

Models are downloaded on first run (~2.5 GB).

---

## Tests

```bash
pytest                    # all 71
pytest -m "not slow"      # skip model-loading tests
```

Includes:
- Exhaustive permission matrix — every role x every permission
- SQL injection attempts against every tool schema
- Full approval journey over HTTP: request -> no change -> approve -> change
- Self-approval, stale-state, double-execution, and invalid-transition guards
- A regression guard that fails if cross-lingual Recall@1 drops below 0.85

---

## Known limitations

- Evaluation set is 12 documents / 24 questions. Directional, not precise.
- Embeddings are stored as JSON text and compared in Python. pgvector is the
  intended replacement once the corpus grows past a few hundred chunks.
- Residual same-language bias at 0.08; two of 24 queries still fail this way.
- Approval expiry is enforced on read, not by a background job.
- Reranker latency not yet measured against the 1.5s p95 target.

---

## Next

The LangGraph agent: tool selection, checkpointed state, and an interrupt that
suspends the run when a sensitive tool is called — so an approval can span a
process restart.

---

## Demo

An Arabic query returning an English source document:

![Cross-lingual search](docs/images/demo.png)

The correct English document scores 0.97; the closest Arabic document scores
0.12. The gap shows the reranker is deciding on meaning, not language.