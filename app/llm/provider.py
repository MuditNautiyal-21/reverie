"""Provider interface for chat-completion LLMs.

Adding a new provider is three steps: subclass LLMProvider, branch on its name
in get_provider, set LLM_PROVIDER in .env.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.config import Settings, get_settings


class LLMProvider(ABC):
    name: str = "abstract"

    @abstractmethod
    def complete(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        response_format_json: bool = False,
    ) -> str: ...


def get_provider(settings: Settings | None = None) -> LLMProvider:
    settings = settings or get_settings()
    name = settings.llm_provider

    if name == "groq":
        from app.llm.groq_provider import GroqProvider

        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not set. Add it to .env.")
        return GroqProvider(api_key=settings.groq_api_key, model=settings.llm_model)

    raise RuntimeError(f"Unknown LLM_PROVIDER '{name}'. Supported: groq.")
