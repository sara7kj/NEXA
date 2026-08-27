# ADR-009: Embedding Model Selection (SPIKE-01)

**Status:** In progress — preliminary findings
**Date:** 2026-08-27

## Context
NEXA needs cross-lingual retrieval: an Arabic query must surface relevant
English passages and vice versa. ARCHITECTURE.md SS14 sets the bar at
cross-lingual Recall@5 >= 0.75.

## Findings (preliminary)

Mini-corpus: 6 documents (3 AR, 3 EN), 10 questions with known answers.
Model: intfloat/multilingual-e5-large.

| Variant | Recall@1 | Same-language bias |
|---|---|---|
| Baseline (query:/passage: prefixes) | 0.50 | 0.90 |
| No prefixes | 0.60 | 0.80 |
| Per-language mean centering | 0.80 | 0.60 |

Note: 0.50 same-language bias is neutral. The baseline picked a
same-language document in 9 of 10 cases, which explains the low Recall@1 —
the model ranks by language before meaning.

Mean centering (subtracting each language's mean vector) reduced the bias
and lifted accuracy. Both columns moved together, supporting the diagnosis.

## Decision
Not final. Findings are directional only.

## Limitations
- 10 questions / 6 documents. One question = 10% swing.
- Mean centering was computed on the same data it was evaluated on
  (overfitting risk). Needs a held-out set.
- Only one model family tested.

## Next steps
- Expand to 20 documents / 30 questions per ARCHITECTURE.md SS14.
- Recompute centering on a held-out split.
- Test at least one alternative model family.
- Report Recall@5 (the actual acceptance metric), not just Recall@1.
