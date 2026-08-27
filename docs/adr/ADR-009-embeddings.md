# ADR-009: Embedding Model and Reranking (SPIKE-01)

**Status:** Accepted
**Date:** 2026-08-27

## Context
NEXA requires cross-lingual retrieval: an Arabic query must surface relevant
English passages and vice versa. ARCHITECTURE.md SS14 sets the acceptance bar
at cross-lingual Recall@5 >= 0.75.

## Method
- Corpus: 12 documents (6 EN, 6 AR). Each topic exists in **one language only**.
- Questions: 24, all strictly cross-lingual, one valid answer each.
- Retrieval: intfloat/multilingual-e5-large.
- Reranking: BAAI/bge-reranker-v2-m3 over the top 5 dense results.

## Results

| Pipeline | Recall@1 | Recall@5 | Same-language bias |
|---|---|---|---|
| Dense only | 0.38 | 0.92 | 0.62 |
| Dense + cross-encoder rerank | **0.92** | - | **0.08** |

Neutral bias is 0.50. Dense retrieval alone favours same-language documents
(0.62) and this caps top-1 accuracy. Reranking removes the effect entirely
(0.08) and lifts Recall@1 from 0.38 to 0.92.

Recall@5 of 0.92 under dense retrieval shows the correct document was almost
always retrieved. The failure was in **ranking**, not retrieval.

## Two corrections made during this spike

**1. Mean centering was overfitting.** An early run reported Recall@1 improving
0.50 -> 0.80 via per-language mean centering. On a held-out split the same
technique scored 0.08. The improvement was not real. Mean centering is rejected.

**2. The evaluation set itself was flawed.** A second dataset paired every topic
with a translated twin, then required the model to select the foreign-language
twin. When an English query was answered from an English document, the harness
scored it wrong - though that is the correct behaviour. Recall@1 of 0.00 was
measuring a broken metric, not a broken system. Inspecting raw reranker scores
exposed this; aggregate numbers alone did not.

## Decisions
1. **Adopt intfloat/multilingual-e5-large** for dense retrieval.
2. **Adopt BAAI/bge-reranker-v2-m3** as the reranking stage.
3. **Promote reranking from V1 to MVP scope.** Dense retrieval alone yields
   Recall@1 of 0.38 on cross-lingual queries, which is not usable. Update
   PRD FR-17 and ARCHITECTURE.md SS7.3 accordingly.
4. **Reject per-language mean centering.** Does not generalize.

## Limitations
- 12 documents, 24 questions. Directional, not precise.
- Clean synthetic corpus with unambiguous topic separation.
- Only one model family tested for each stage.
- Reranker latency not yet measured against NFR-03 (1.5s p95).

## Follow-up
- Re-measure once the full 30-50 document corpus exists.
- Measure reranker latency and confirm NFR-03 compliance.
