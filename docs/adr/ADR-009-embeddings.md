# ADR-009: Embedding Model Selection (SPIKE-01)

**Status:** In progress
**Date:** 2026-08-27 (revised)

## Context
NEXA requires cross-lingual retrieval: an Arabic query must surface relevant
English passages and vice versa. ARCHITECTURE.md SS14 sets the bar at
cross-lingual Recall@5 >= 0.75.

## Method
- Corpus: 12 documents (6 AR, 6 EN), paired by topic.
- Questions: 24, all strictly cross-lingual (AR query -> EN source, EN query -> AR source).
- Split: even-indexed questions used to compute mean centering, odd-indexed held out for evaluation (12 test questions).
- Model: intfloat/multilingual-e5-large.

## Findings

| Variant | Recall@1 | Recall@5 | Same-language bias |
|---|---|---|---|
| Baseline | 0.00 | 0.83 | 1.00 |
| Per-language mean centering (held-out) | 0.08 | 1.00 | 0.92 |

Neutral bias would be 0.50. At 1.00, the model selected a same-language
document for every single query. The bias is not a tendency, it is absolute.

**Correction to earlier findings.** A first pass on a smaller set reported
Recall@1 improving 0.50 -> 0.80 under mean centering. That result did not
survive a held-out split: centering computed on separate questions yields
0.08. The earlier number was overfitting, not signal.

## Interpretation
Recall@5 is high (0.83 baseline, 1.00 centered) while Recall@1 is near zero.
The correct document is reliably retrieved but consistently outranked by a
same-language document. This is a **ranking** failure, not a retrieval failure.

## Decision
Retain multilingual-e5-large as the retrieval model. Its Recall@5 already
meets the SS14 acceptance bar.

Promote the reranking stage from a V1 enhancement to an **MVP requirement**.
Dense retrieval alone cannot produce a usable top-1 result on cross-lingual
queries in this corpus.

Do not adopt mean centering. It does not generalize.

## Limitations
- 12 documents, 12 held-out questions. Directional, not precise.
- Only one model family tested.
- Synthetic corpus with clean topic pairing; real documents are messier.

## Next steps
- Measure a cross-encoder reranker over the top-5. Target: Recall@1 >= 0.75.
- Update ARCHITECTURE.md SS7.3 and PRD FR-17 to move reranking into MVP scope.
- Test one alternative model family for comparison.
