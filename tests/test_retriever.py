import sys

import pytest

pytestmark = pytest.mark.slow

sys.path.insert(0, "spikes")
from dataset_v3 import DOCS, QUESTIONS

from nexa.rag.retriever import Retriever


@pytest.fixture(scope="module")
def retriever() -> Retriever:
    r = Retriever()
    r.index(DOCS)
    return r


def test_search_before_index_raises() -> None:
    with pytest.raises(RuntimeError):
        Retriever().search("anything")


def test_returns_requested_number_of_results(retriever: Retriever) -> None:
    assert len(retriever.search("annual leave", top_k=3)) == 3


def test_cross_lingual_recall_at_1(retriever: Retriever) -> None:
    hits = sum(retriever.search(q)[0].doc_id == want for q, want in QUESTIONS)
    recall = hits / len(QUESTIONS)
    assert recall >= 0.85, f"Recall@1 regressed to {recall:.2f}"
