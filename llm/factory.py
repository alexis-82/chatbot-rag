from __future__ import annotations

import config
from llm.anthropic_provider import AnthropicProvider
from llm.base import LLMProvider
from llm.ollama_provider import OllamaProvider
from llm.openai_provider import OpenAIProvider


def get_llm() -> LLMProvider:
    p = config.LLM_PROVIDER
    if p == "ollama":
        return OllamaProvider(model=config.OLLAMA_MODEL, base_url=config.OLLAMA_BASE_URL)
    if p == "anthropic":
        return AnthropicProvider(model=config.ANTHROPIC_MODEL, api_key=config.ANTHROPIC_API_KEY)
    if p == "openai":
        return OpenAIProvider(model=config.OPENAI_MODEL, api_key=config.OPENAI_API_KEY)
    raise ValueError(f"LLM_PROVIDER non valido: {p}")
