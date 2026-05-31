"""Database connection and schema bootstrap.

Connects to Postgres via psycopg 3 using DATABASE_URL from .env. The pgvector
extension must be enabled in the target database (Supabase enables it via the
extensions UI).
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Iterator

import psycopg
from pgvector.psycopg import register_vector

from app.config import get_settings

log = logging.getLogger(__name__)


def _resolve_dsn() -> str:
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not set. Add it to .env.")
    return settings.database_url


@contextmanager
def get_conn() -> Iterator[psycopg.Connection]:
    dsn = _resolve_dsn()
    with psycopg.connect(dsn) as conn:
        register_vector(conn)
        yield conn


def init_schema() -> None:
    settings = get_settings()
    dim = settings.embedding_dim

    ddl = f"""
        create extension if not exists vector;

        create table if not exists memories (
            id        integer primary key,
            date      date    not null,
            text      text    not null,
            mood      text    not null,
            themes    jsonb   not null default '[]'::jsonb,
            tags      jsonb   not null default '[]'::jsonb,
            summary   text    not null,
            embedding vector({dim}) not null
        );

        create index if not exists memories_embedding_hnsw
            on memories using hnsw (embedding vector_cosine_ops);

        create index if not exists memories_date_idx on memories (date);
        create index if not exists memories_mood_idx on memories (mood);
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
        conn.commit()
    log.info("Schema ready (dim=%d).", dim)
