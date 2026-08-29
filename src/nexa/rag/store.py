import json

from sqlalchemy.orm import Session

from nexa.db.connection import engine
from nexa.db.models import Chunk
from nexa.rag.retriever import Retriever


def load_retriever() -> Retriever:
    with Session(engine) as session:
        chunks = session.query(Chunk).all()
        if not chunks:
            raise RuntimeError("no chunks in database - run seed.py first")

        documents = {c.document_id: c.content for c in chunks}
        embeddings = [json.loads(c.embedding) for c in chunks]

    retriever = Retriever()
    retriever.load(documents, embeddings)
    return retriever
