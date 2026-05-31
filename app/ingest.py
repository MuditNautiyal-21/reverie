"""Load raw journal entries from disk."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.config import ENTRIES_PATH


@dataclass(frozen=True)
class Entry:
    id: int
    date: str
    text: str


def load_entries(path: Path | None = None) -> list[Entry]:
    path = path or ENTRIES_PATH
    if not path.exists():
        raise FileNotFoundError(f"Entries file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, list):
        raise ValueError("entries.json must be a top-level JSON array.")

    entries: list[Entry] = []
    seen_ids: set[int] = set()
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"Entry {i} is not an object.")
        for key in ("id", "date", "text"):
            if key not in item:
                raise ValueError(f"Entry {i} missing required key '{key}'.")
        eid = int(item["id"])
        if eid in seen_ids:
            raise ValueError(f"Duplicate entry id: {eid}")
        seen_ids.add(eid)
        entries.append(Entry(id=eid, date=str(item["date"]), text=str(item["text"])))

    entries.sort(key=lambda e: (e.date, e.id))
    return entries
