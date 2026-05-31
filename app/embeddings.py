"""Local sentence-transformers embeddings.

The model is loaded once and cached in module state. First call pays the
download cost; subsequent calls are fast.
"""

from __future__ import annotations

import logging
from threading import Lock
from typing import Iterable

from app.config import get_settings

log = logging.getLogger(__name__)

_model = None
_model_lock = Lock()


def _load_model():
    global _model
    if _model is not None:
        return _model
    with _model_lock:
        if _model is None:
            from sentence_transformers import SentenceTransformer

            name = get_settings().embedding_model
            log.info("Loading embedding model: %s", name)
            _model = SentenceTransformer(name)
    return _model


def embed(text: str) -> list[float]:
    if not isinstance(text, str):
        raise TypeError("embed() expects a str")
    vec = _load_model().encode(text, normalize_embeddings=True, convert_to_numpy=True)
    return vec.tolist()


def embed_batch(texts: Iterable[str]) -> list[list[float]]:
    items = list(texts)
    if not items:
        return []
    vecs = _load_model().encode(
        items,
        normalize_embeddings=True,
        convert_to_numpy=True,
        batch_size=32,
        show_progress_bar=False,
    )
    return [v.tolist() for v in vecs]
