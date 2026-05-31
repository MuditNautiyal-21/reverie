"""Answer a question grounded in the retrieved journal entries.

The pipeline over-fetches candidates from pgvector, then asks the LLM to do
two jobs in one call: pick which entries actually answer the question, and
write a short second-person reply that draws only on those. Citations are
attached server-side from the fetched rows so the model cannot invent text.

Run from the project root:

    python -m app.answer "how did I feel about Maya after she left"
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from typing import Any

from app.llm import get_provider
from app.search import Hit, search

log = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "You are Reverie, a warm and honest reader of someone's personal journal. "
    "You are given a question the writer is asking themselves, and a set of "
    "candidate journal entries retrieved from their archive. Each entry has "
    "an id, a date, a mood, and the full text.\n\n"
    "Your job is two things in one reply:\n"
    "  1. Decide which of the candidate entries actually help answer the "
    "question, and ignore the ones that do not. Some candidates may be "
    "topically close but wrong for the question (for example, an entry about "
    "a low point is not an answer to 'when did things turn around'). Use "
    "judgment, not just topical overlap.\n"
    "  2. Write a short reply, one short paragraph or two, addressed to the "
    "writer as 'you'. Be warm and honest. Not clinical, not therapy-speak, "
    "not flattering. Reference dates naturally ('back in early October', "
    "'around mid-November'), not as timestamps. Use only what is in the "
    "selected entries; never invent facts, names, or feelings the entries "
    "do not contain. If the entries genuinely do not answer the question, "
    "say so gently and stop there rather than guessing.\n\n"
    "Return STRICT JSON ONLY, no prose, no markdown, no code fences, with "
    "exactly these two keys:\n"
    "  {\n"
    "    \"answer\": \"the short reply, addressed to the writer as 'you'\",\n"
    "    \"cited_ids\": [the integer ids of the entries the answer actually "
    "draws on, in the order they're referenced]\n"
    "  }\n"
    "Do not include any entry id in cited_ids unless your answer actually "
    "draws on that entry. If the entries don't answer the question, return "
    "an empty cited_ids array and say so in the answer."
)


def _format_candidates_for_prompt(hits: list[Hit]) -> str:
    lines: list[str] = []
    for h in hits:
        lines.append(f"--- entry id={h.id} | date={h.date} | mood={h.mood} ---\n{h.text}")
    return "\n\n".join(lines)


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


def _validate(obj: dict[str, Any]) -> tuple[str, list[int]] | None:
    if "answer" not in obj or "cited_ids" not in obj:
        return None
    answer = obj["answer"]
    cited = obj["cited_ids"]
    if not isinstance(answer, str) or not answer.strip():
        return None
    if not isinstance(cited, list):
        return None
    cleaned_ids: list[int] = []
    for x in cited:
        try:
            cleaned_ids.append(int(x))
        except (TypeError, ValueError):
            return None
    return answer.strip(), cleaned_ids


def answer_question(question: str, top_k: int = 5) -> dict[str, Any]:
    if not question or not question.strip():
        return {"answer": "", "citations": [], "candidates_considered": 0}

    # Over-fetch so the model can drop topically-close-but-wrong candidates.
    over_fetch = max(top_k * 3, top_k)
    candidates = search(question, top_k=over_fetch)

    if not candidates:
        return {
            "answer": (
                "I don't have anything in your journal that touches this. "
                "Try asking it a different way, or about something specific you "
                "remember writing about."
            ),
            "citations": [],
            "candidates_considered": 0,
        }

    candidates_by_id: dict[int, Hit] = {h.id: h for h in candidates}

    user_msg = (
        f"Question:\n{question.strip()}\n\n"
        f"Candidate entries ({len(candidates)} of them):\n\n"
        f"{_format_candidates_for_prompt(candidates)}\n\n"
        "Return the JSON object."
    )

    provider = get_provider()

    for attempt in (1, 2):
        try:
            raw = provider.complete(
                system=SYSTEM_PROMPT,
                user=user_msg,
                temperature=0.4,
                max_tokens=900,
                response_format_json=True,
            )
        except Exception as exc:
            log.warning("answer LLM call attempt %s failed: %s", attempt, exc)
            if attempt == 2:
                raise
            continue

        parsed = _extract_json(raw)
        if parsed is None:
            log.warning("answer attempt %s produced invalid JSON.", attempt)
            continue
        validated = _validate(parsed)
        if validated is None:
            log.warning("answer attempt %s JSON missing required keys.", attempt)
            continue
        answer_text, cited_ids = validated
        break
    else:
        raise RuntimeError("LLM did not return valid JSON for the answer.")

    # Map cited ids back to fetched rows; silently drop any id not in the
    # candidate set so the model cannot fabricate citations.
    citations: list[dict[str, Any]] = []
    seen: set[int] = set()
    for cid in cited_ids:
        if cid in seen:
            continue
        hit = candidates_by_id.get(cid)
        if hit is None:
            log.warning("model cited id=%s not in candidates; dropping.", cid)
            continue
        seen.add(cid)
        citations.append({"id": hit.id, "date": hit.date, "text": hit.text, "mood": hit.mood})

    return {
        "answer": answer_text,
        "citations": citations,
        "candidates_considered": len(candidates),
    }


def _print_result(question: str, result: dict[str, Any]) -> None:
    print(f"\nQuestion: {question}")
    print("=" * (10 + len(question)))
    print(f"\n{result['answer']}\n")

    cits = result.get("citations", [])
    if not cits:
        print("(no entries cited)")
        return

    print(f"Citations ({len(cits)} of {result.get('candidates_considered', '?')} considered):")
    for c in cits:
        snippet = c["text"].replace("\n", " ")
        if len(snippet) > 140:
            snippet = snippet[:137] + "..."
        print(f"  - id={c['id']}  {c['date']}  mood={c['mood']}")
        print(f"      {snippet}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ask your memories.")
    parser.add_argument("question", type=str)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args(argv)

    try:
        result = answer_question(args.question, top_k=args.top_k)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    _print_result(args.question, result)
    return 0


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(message)s",
        datefmt="%H:%M:%S",
    )
    sys.exit(main())
