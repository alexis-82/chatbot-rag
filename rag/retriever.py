from __future__ import annotations

from langchain_chroma import Chroma
from langchain_core.documents import Document


def retrieve(vs: Chroma, query: str, top_k: int) -> list[Document]:
    return vs.similarity_search(query, k=top_k)
