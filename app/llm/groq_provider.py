"""Groq chat-completion provider.

Talks to Groq's OpenAI-compatible REST endpoint directly so we avoid pulling
in the full OpenAI SDK. Honours the Retry-After header on 429 responses and
falls back to exponential backoff.
"""

from __future__ import annotations

import logging
import time

import httpx

from app.llm.provider import LLMProvider

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

log = logging.getLogger(__name__)


class GroqProvider(LLMProvider):
    name = "groq"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout: float = 60.0,
        max_rate_limit_retries: int = 5,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._max_rate_limit_retries = max_rate_limit_retries

    def complete(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        response_format_json: bool = False,
    ) -> str:
        payload: dict = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format_json:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=self._timeout) as client:
            for attempt in range(self._max_rate_limit_retries + 1):
                resp = client.post(GROQ_CHAT_URL, headers=headers, json=payload)
                if resp.status_code != 429:
                    resp.raise_for_status()
                    data = resp.json()
                    break

                wait_s = self._compute_backoff(resp, attempt)
                if attempt == self._max_rate_limit_retries:
                    log.warning("Groq 429 after %d retries.", attempt)
                    resp.raise_for_status()
                log.info("Groq 429, sleeping %.2fs.", wait_s)
                time.sleep(wait_s)

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError(f"Unexpected Groq response shape: {data}") from exc

    @staticmethod
    def _compute_backoff(resp: httpx.Response, attempt: int) -> float:
        retry_after = resp.headers.get("retry-after")
        if retry_after:
            try:
                return max(float(retry_after), 0.5)
            except ValueError:
                pass
        return min(2 ** attempt, 30.0)
