"""Enrich each journal entry with mood, themes, tags, and a one-line summary.

Run from the project root:

    python -m app.enrich

The script loads data/entries.json, asks the LLM for strict JSON per entry,
parses with one retry, skips on second failure, and writes the merged result
to data/enriched.json. Resumes from any existing enriched.json so a re-run
only processes entries that were skipped or are new.
"""

from __future__ import annotations

import json
import logging
import re
import sys
import time
from dataclasses import asdict
from typing import Any

from app.config import ENRICHED_PATH, get_settings
from app.ingest import Entry, load_entries
from app.llm import LLMProvider, get_provider

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("enrich")


SYSTEM_PROMPT = (
    "You are a careful assistant that reads a single private journal entry "
    "and tags it for later retrieval. You return STRICT JSON ONLY, with no "
    "prose, no markdown, no commentary, no code fences. The JSON object MUST "
    "have exactly these keys: mood (string, one or two words), themes (array "
    "of broad recurring topic strings like 'relationship', 'work', 'money', "
    "'writing', 'running'), tags (array of specific concrete strings actually "
    "mentioned in the entry, such as people's names, projects, places, or "
    "objects), and summary (a single short sentence capturing the entry). "
    "Keep themes broad and reusable across many entries. Keep tags specific "
    "and grounded in the actual text. Do not invent facts."
)

USER_TEMPLATE = (
    "Entry date: {date}\n"
    "Entry text:\n"
    "\"\"\"\n{text}\n\"\"\"\n\n"
    "Return only the JSON object."
)

REQUIRED_KEYS = ("mood", "themes", "tags", "summary")


def _extract_json(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    candidate = text.strip()

    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", candidate, re.DOTALL)
    if fence:
        candidate = fence.group(1)
    else:
        first = candidate.find("{")
        last = candidate.rfind("}")
        if first != -1 and last != -1 and last > first:
            candidate = candidate[first : last + 1]

    try:
        obj = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def _validate(obj: dict[str, Any]) -> dict[str, Any] | None:
    for key in REQUIRED_KEYS:
        if key not in obj:
            return None

    mood = obj["mood"]
    themes = obj["themes"]
    tags = obj["tags"]
    summary = obj["summary"]

    if not isinstance(mood, str) or not mood.strip():
        return None
    if not isinstance(summary, str) or not summary.strip():
        return None
    if not isinstance(themes, list) or not all(isinstance(t, str) for t in themes):
        return None
    if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
        return None

    return {
        "mood": mood.strip(),
        "themes": [t.strip() for t in themes if t.strip()],
        "tags": [t.strip() for t in tags if t.strip()],
        "summary": summary.strip(),
    }


def enrich_one(provider: LLMProvider, entry: Entry) -> dict[str, Any] | None:
    user_msg = USER_TEMPLATE.format(date=entry.date, text=entry.text)

    for attempt in (1, 2):
        try:
            raw = provider.complete(
                system=SYSTEM_PROMPT,
                user=user_msg,
                temperature=0.2,
                max_tokens=400,
                response_format_json=True,
            )
        except Exception as exc:
            log.warning("entry %s attempt %s transport error: %s", entry.id, attempt, exc)
            if attempt == 2:
                return None
            time.sleep(1.0)
            continue

        parsed = _extract_json(raw)
        if parsed is not None:
            validated = _validate(parsed)
            if validated is not None:
                return validated

        log.warning("entry %s attempt %s produced invalid JSON.", entry.id, attempt)
        if attempt == 2:
            return None
        time.sleep(0.5)

    return None


def _load_existing() -> dict[int, dict[str, Any]]:
    if not ENRICHED_PATH.exists():
        return {}
    try:
        with ENRICHED_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, list):
        return {}
    out: dict[int, dict[str, Any]] = {}
    for item in data:
        if isinstance(item, dict) and "id" in item and all(k in item for k in REQUIRED_KEYS):
            out[int(item["id"])] = item
    return out


def run() -> int:
    settings = get_settings()
    log.info("Using provider=%s model=%s", settings.llm_provider, settings.llm_model)

    try:
        provider = get_provider(settings)
    except RuntimeError as exc:
        log.error(str(exc))
        return 2

    entries = load_entries()
    log.info("Loaded %d entries.", len(entries))

    existing = _load_existing()
    if existing:
        log.info("Resuming: %d entries already enriched.", len(existing))

    # Stay under Groq's free-tier per-minute limit without coordination logic.
    inter_entry_sleep = 1.2

    enriched_by_id: dict[int, dict[str, Any]] = dict(existing)
    skipped: list[int] = []

    for i, entry in enumerate(entries, start=1):
        if entry.id in existing:
            log.info("[%d/%d] entry %d already enriched.", i, len(entries), entry.id)
            continue

        log.info("[%d/%d] enriching entry %d (%s)...", i, len(entries), entry.id, entry.date)
        result = enrich_one(provider, entry)
        if result is None:
            log.warning("[%d/%d] skipping entry %d after retries.", i, len(entries), entry.id)
            skipped.append(entry.id)
            continue
        enriched_by_id[entry.id] = {**asdict(entry), **result}
        log.info(
            "  mood=%s  themes=%s  tags=%s",
            result["mood"], result["themes"], result["tags"],
        )
        time.sleep(inter_entry_sleep)

    enriched_ordered = [enriched_by_id[e.id] for e in entries if e.id in enriched_by_id]

    ENRICHED_PATH.parent.mkdir(parents=True, exist_ok=True)
    with ENRICHED_PATH.open("w", encoding="utf-8") as f:
        json.dump(enriched_ordered, f, ensure_ascii=False, indent=2)

    log.info("Wrote %d enriched entries to %s", len(enriched_ordered), ENRICHED_PATH)
    if skipped:
        log.warning("Skipped %d entries: %s", len(skipped), skipped)
    return 0 if not skipped else 1


if __name__ == "__main__":
    sys.exit(run())
