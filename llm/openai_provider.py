from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from llm.base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self, model: str, api_key: str) -> None:
        self._client = ChatOpenAI(model=model, api_key=api_key)

    def chat(self, system: str, user: str) -> str:
        resp = self._client.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        return resp.content if isinstance(resp.content, str) else str(resp.content)
