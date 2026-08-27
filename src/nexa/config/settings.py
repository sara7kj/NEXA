from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    embedding_model: str = "intfloat/multilingual-e5-large"
    reranker_model: str = "BAAI/bge-reranker-v2-m3"

    query_prefix: str = "query: "
    passage_prefix: str = "passage: "

    retrieve_top_k: int = 5
    rerank_top_n: int = 1


settings = Settings()
