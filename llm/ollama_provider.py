from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from llm.base import LLMProvider


class OllamaProvider(LLMProvider):
    def __init__(self, model: str, base_url: str) -> None:
        self._client = ChatOllama(
            model=model,
            base_url=base_url,
            num_ctx=8192,
            num_predict=1024,
        )

    def chat(self, system: str, user: str) -> str:
        resp = self._client.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        return resp.content if isinstance(resp.content, str) else str(resp.content)
