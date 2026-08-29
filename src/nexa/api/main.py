from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from nexa.rag.store import load_retriever

state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    state["retriever"] = load_retriever()
    yield
    state.clear()


app = FastAPI(title="NEXA", version="0.1.0", lifespan=lifespan)


class SearchHit(BaseModel):
    doc_id: str
    content: str
    score: float


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/search", response_model=list[SearchHit])
def search(q: str = Query(min_length=3, max_length=500)) -> list[SearchHit]:
    retriever = state.get("retriever")
    if retriever is None:
        raise HTTPException(status_code=503, detail="retriever not ready")

    return [
        SearchHit(doc_id=r.doc_id, content=r.content, score=r.score)
        for r in retriever.search(q)
    ]
