import os
from dataclasses import dataclass, field
from pathlib import Path


def _load_env() -> None:
    env = Path(".env")
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


_load_env()


@dataclass(frozen=True)
class Settings:
    embedding_model: str = "intfloat/multilingual-e5-large"
    reranker_model: str = "BAAI/bge-reranker-v2-m3"

    query_prefix: str = "query: "
    passage_prefix: str = "passage: "

    retrieve_top_k: int = 5
    rerank_top_n: int = 1

    token_expiry_minutes: int = 30

    jwt_secret: str = field(
        default_factory=lambda: os.environ["JWT_SECRET"]
    )


settings = Settings()