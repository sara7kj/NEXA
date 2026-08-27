from dataclasses import dataclass

import numpy as np
from sentence_transformers import CrossEncoder, SentenceTransformer, util

from nexa.config.settings import settings


@dataclass(frozen=True)
class SearchResult:
    doc_id: str
    content: str
    score: float


class Retriever:
    def __init__(self) -> None:
        self._bi = SentenceTransformer(settings.embedding_model)
        self._ce = CrossEncoder(settings.reranker_model)
        self._ids: list[str] = []
        self._texts: list[str] = []
        self._embeddings = None

    def index(self, documents: dict[str, str]) -> None:
        self._ids = list(documents.keys())
        self._texts = [documents[k] for k in self._ids]
        self._embeddings = self._bi.encode(
            [settings.passage_prefix + t for t in self._texts]
        )

    def search(self, query: str, top_k: int | None = None) -> list[SearchResult]:
        if self._embeddings is None:
            raise RuntimeError("index() must be called before search()")

        k = top_k or settings.retrieve_top_k
        q_emb = self._bi.encode(settings.query_prefix + query)
        scores = util.cos_sim(q_emb, self._embeddings)[0]
        top = [int(i) for i in scores.argsort(descending=True)[:k]]

        pairs = [(query, self._texts[i]) for i in top]
        rerank_scores = self._ce.predict(pairs)
        order = np.argsort(rerank_scores)[::-1]

        return [
            SearchResult(
                doc_id=self._ids[top[i]],
                content=self._texts[top[i]],
                score=float(rerank_scores[i]),
            )
            for i in order
        ]
