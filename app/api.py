"""HTTP surface for Reverie.

    GET  /health   liveness probe
    POST /ask      grounded, cited answer to a question

Run locally:

    uvicorn app.api:app --reload
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.answer import answer_question

log = logging.getLogger(__name__)

app = FastAPI(
    title="Reverie",
    version="0.1.0",
    description="Ask your memories. Warm, honest, cited answers from your journal.",
)

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=15)


class Citation(BaseModel):
    id: int
    date: str
    text: str
    mood: str


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    candidates_considered: int


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    try:
        result = answer_question(req.question, top_k=req.top_k)
    except RuntimeError as exc:
        log.exception("answer_question failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        log.exception("unexpected error in /ask")
        raise HTTPException(status_code=500, detail="internal error") from exc

    return AskResponse(
        answer=result["answer"],
        citations=[Citation(**c) for c in result["citations"]],
        candidates_considered=result["candidates_considered"],
    )
