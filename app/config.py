"""Environment and path configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DATA_DIR = PROJECT_ROOT / "data"
ENTRIES_PATH = DATA_DIR / "entries.json"
ENRICHED_PATH = DATA_DIR / "enriched.json"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


@dataclass(frozen=True)
class Settings:
    llm_provider: str
    llm_model: str
    groq_api_key: str | None
    database_url: str | None
    embedding_model: str
    embedding_dim: int


def get_settings() -> Settings:
    return Settings(
        llm_provider=os.getenv("LLM_PROVIDER", "groq").strip().lower(),
        llm_model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile").strip(),
        groq_api_key=os.getenv("GROQ_API_KEY") or None,
        database_url=os.getenv("DATABASE_URL") or None,
        embedding_model=os.getenv("EMBEDDING_MODEL", EMBEDDING_MODEL_NAME).strip(),
        embedding_dim=int(os.getenv("EMBEDDING_DIM", EMBEDDING_DIM)),
    )
