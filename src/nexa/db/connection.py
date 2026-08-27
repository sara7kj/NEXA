import os

from sqlalchemy import create_engine, text


def _database_url() -> str:
    for line in open(".env", encoding="utf-8"):
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("DATABASE_URL not found in .env")


engine = create_engine(_database_url())


def check_connection() -> str:
    with engine.connect() as conn:
        return conn.execute(text("SELECT version()")).scalar_one()
