"""Semantic retrieval over the memories index.

Usage from the CLI:

    python -m app.search "how did I feel about Maya after she left"
    python -m app.search "when did things start to turn around" --top-k 5

Similarity is returned in [-1, 1], higher is closer. Internally we order by
pgvector's cosine distance ascending and compute similarity = 1 - distance.
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from typing import Any

from app.db import get_conn
from app.embeddings import embed

log = logging.getLogger(__name__)


@dataclass
class Hit:
    id: int
    date: str
    text: str
    mood: str
    themes: list[str]
    tags: list[str]
    summary: str
    similarity: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "date": self.date,
            "text": self.text,
            "mood": self.mood,
            "themes": self.themes,
            "tags": self.tags,
            "summary": self.summary,
            "similarity": self.similarity,
        }


def search(query: str, top_k: int = 5, mood: str | None = None) -> list[Hit]:
    if not query or not query.strip():
        return []

    qvec = embed(query)

    sql = """
        select
            id, date, text, mood, themes, tags, summary,
            1 - (embedding <=> %s::vector) as similarity
        from memories
        {where}
        order by embedding <=> %s::vector
        limit %s
    """
    params: list[Any] = [qvec]
    where = ""
    if mood:
        where = "where mood = %s"
        params.append(mood.strip().lower())
    params.append(qvec)
    params.append(int(top_k))

    sql = sql.format(where=where)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

    hits: list[Hit] = []
    for row in rows:
        eid, edate, etext, emood, ethemes, etags, esummary, sim = row
        hits.append(
            Hit(
                id=int(eid),
                date=edate.isoformat() if hasattr(edate, "isoformat") else str(edate),
                text=etext,
                mood=emood,
                themes=list(ethemes or []),
                tags=list(etags or []),
                summary=esummary,
                similarity=float(sim),
            )
        )
    return hits


def _print_hits(query: str, hits: list[Hit]) -> None:
    print(f"\nQuery: {query}")
    print("=" * (8 + len(query)))
    if not hits:
        print("(no results)")
        return
    for rank, h in enumerate(hits, start=1):
        snippet = h.text.replace("\n", " ")
        if len(snippet) > 220:
            snippet = snippet[:217] + "..."
        print(f"\n#{rank}  id={h.id}  date={h.date}  mood={h.mood}  sim={h.similarity:.3f}")
        print(f"     themes: {', '.join(h.themes) or '-'}")
        print(f"     tags:   {', '.join(h.tags) or '-'}")
        print(f"     {snippet}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Semantic search over memories.")
    parser.add_argument("query", type=str)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--mood", type=str, default=None)
    args = parser.parse_args(argv)

    try:
        hits = search(args.query, top_k=args.top_k, mood=args.mood)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    _print_hits(args.query, hits)
    return 0


if __name__ == "__main__":
    sys.exit(main())
