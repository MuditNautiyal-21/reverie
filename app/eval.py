"""Retrieval evaluation harness.

Reads a labelled question set from data/eval_questions.json and reports
per-question hit and recall@k, plus an overall hit rate and mean recall.
No LLM is involved.

    python -m app.eval
    python -m app.eval --top-k 10
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from app.config import DATA_DIR
from app.search import search

EVAL_PATH: Path = DATA_DIR / "eval_questions.json"


@dataclass
class QResult:
    question: str
    expected: list[int]
    retrieved: list[int]
    hit: int
    recall: float


def _load_questions() -> list[dict]:
    if not EVAL_PATH.exists():
        raise FileNotFoundError(f"Eval set not found: {EVAL_PATH}")
    with EVAL_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("eval_questions.json must be a JSON array.")
    for i, item in enumerate(data):
        if not isinstance(item, dict) or "question" not in item or "expected_ids" not in item:
            raise ValueError(f"Eval item {i} must have 'question' and 'expected_ids'.")
    return data


def _evaluate_one(question: str, expected_ids: list[int], top_k: int) -> QResult:
    expected_set = set(int(x) for x in expected_ids)
    hits = search(question, top_k=top_k)
    retrieved = [h.id for h in hits]
    retrieved_set = set(retrieved)

    overlap = expected_set & retrieved_set
    hit = 1 if overlap else 0
    recall = (len(overlap) / len(expected_set)) if expected_set else 0.0

    return QResult(question=question, expected=list(expected_ids),
                   retrieved=retrieved, hit=hit, recall=recall)


def _format_id_list(ids: list[int], highlight: set[int]) -> str:
    parts = []
    for i in ids:
        if i in highlight:
            parts.append(f"\033[32m{i}\033[0m")
        else:
            parts.append(str(i))
    return "[" + ", ".join(parts) + "]"


def run(top_k: int = 5) -> int:
    questions = _load_questions()

    print(f"\nReverie retrieval eval  ·  k={top_k}  ·  {len(questions)} questions")
    print("=" * 78)

    results: list[QResult] = []
    for q in questions:
        r = _evaluate_one(q["question"], q["expected_ids"], top_k)
        results.append(r)

        expected_set = set(r.expected)
        retrieved_set = set(r.retrieved)
        overlap = expected_set & retrieved_set

        print()
        print(f"Q: {r.question}")
        print(f"   expected:  {_format_id_list(r.expected, overlap)}")
        print(f"   retrieved: {_format_id_list(r.retrieved, overlap)}")
        print(
            f"   hit: {r.hit}   recall@{top_k}: {r.recall:.2f}   "
            f"({len(overlap)}/{len(expected_set)} expected ids in top-{top_k})"
        )

    n = len(results)
    if n == 0:
        print("\nNo questions to evaluate.")
        return 1

    hit_rate = sum(r.hit for r in results) / n
    mean_recall = sum(r.recall for r in results) / n

    print()
    print("-" * 78)
    print(
        f"Overall:  hit rate = {hit_rate:.2f}  "
        f"({sum(r.hit for r in results)}/{n})   "
        f"mean recall@{top_k} = {mean_recall:.2f}"
    )
    print()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reverie retrieval eval.")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args(argv)
    return run(top_k=args.top_k)


if __name__ == "__main__":
    sys.exit(main())
