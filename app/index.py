"""Build or refresh the memories index in Postgres.

Run from the project root:

    python -m app.index

Reads data/enriched.json, embeds each entry locally, and upserts rows into
the memories table by id, so re-running refreshes embeddings without
duplicating.
"""

from __future__ import annotations

import json
import logging
import sys

from psycopg.types.json import Jsonb

from app.config import ENRICHED_PATH, get_settings
from app.db import get_conn, init_schema
from app.embeddings import embed_batch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("index")


REQUIRED_KEYS = ("id", "date", "text", "mood", "themes", "tags", "summary")


def _load_enriched() -> list[dict]:
    if not ENRICHED_PATH.exists():
        raise FileNotFoundError(
            f"{ENRICHED_PATH} not found. Run `python -m app.enrich` first."
        )
    with ENRICHED_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("enriched.json must be a JSON array.")
    cleaned: list[dict] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Enriched item {i} is not an object.")
        for k in REQUIRED_KEYS:
            if k not in item:
                raise ValueError(f"Enriched item {i} missing key '{k}'.")
        cleaned.append(item)
    return cleaned


def run() -> int:
    settings = get_settings()
    if not settings.database_url:
        log.error("DATABASE_URL is not set. Add it to .env.")
        return 2

    log.info("Initialising schema...")
    init_schema()

    items = _load_enriched()
    log.info("Loaded %d enriched entries.", len(items))

    log.info("Embedding %d entries with %s ...", len(items), settings.embedding_model)
    vectors = embed_batch([it["text"] for it in items])

    if vectors and len(vectors[0]) != settings.embedding_dim:
        log.error(
            "Embedding dimension mismatch: model produced %d, schema expects %d.",
            len(vectors[0]), settings.embedding_dim,
        )
        return 2

    log.info("Upserting %d rows into memories...", len(items))
    upsert_sql = """
        insert into memories (id, date, text, mood, themes, tags, summary, embedding)
        values (%s, %s, %s, %s, %s, %s, %s, %s)
        on conflict (id) do update set
            date      = excluded.date,
            text      = excluded.text,
            mood      = excluded.mood,
            themes    = excluded.themes,
            tags      = excluded.tags,
            summary   = excluded.summary,
            embedding = excluded.embedding
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            for item, vec in zip(items, vectors):
                cur.execute(
                    upsert_sql,
                    (
                        int(item["id"]),
                        item["date"],
                        item["text"],
                        str(item["mood"]).strip().lower(),
                        Jsonb(item.get("themes", []) or []),
                        Jsonb(item.get("tags", []) or []),
                        item["summary"],
                        vec,
                    ),
                )
        conn.commit()

        with conn.cursor() as cur:
            cur.execute("select count(*) from memories")
            (count,) = cur.fetchone()
    log.info("Done. memories now contains %d rows.", count)
    return 0


if __name__ == "__main__":
    sys.exit(run())
