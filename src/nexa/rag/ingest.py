import json
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from nexa.config.settings import settings
from nexa.db.connection import engine
from nexa.db.models import Chunk, Document
from nexa.rag.chunker import chunk_by_heading, parse_front_matter

DOCUMENTS_DIR = Path("data/documents")


def ingest() -> None:
    files = sorted(DOCUMENTS_DIR.glob("*.md"))
    if not files:
        raise RuntimeError(f"no documents found in {DOCUMENTS_DIR}")

    model = SentenceTransformer(settings.embedding_model)

    with Session(engine) as session:
        session.query(Chunk).delete()
        session.query(Document).delete()

        total_chunks = 0

        for path in files:
            raw = path.read_text(encoding="utf-8")
            meta, body = parse_front_matter(raw)
            pieces = chunk_by_heading(body)

            if not pieces:
                print(f"  skipped (empty): {path.name}")
                continue

            vectors = model.encode(
                [settings.passage_prefix + p.content for p in pieces]
            )

            document = Document(
                id=path.stem,
                title=meta.get("title", path.stem),
                language=meta.get("language", "en"),
                content=body.strip(),
            )

            for piece, vector in zip(pieces, vectors):
                document.chunks.append(
                    Chunk(
                        content=piece.content,
                        embedding=json.dumps(vector.tolist()),
                    )
                )

            session.add(document)
            total_chunks += len(pieces)
            print(f"  {path.name}: {len(pieces)} chunks")

        session.commit()

    print(f"\ningested {len(files)} documents, {total_chunks} chunks")


if __name__ == "__main__":
    ingest()
