from __future__ import annotations

from langchain_chroma import Chroma
from langchain_core.documents import Document


def retrieve(vs: Chroma, query: str, top_k: int) -> list[Document]:
    """Retrieval con MMR: bilancia similarità e diversità delle fonti.

    `fetch_k` è la dimensione del pool di candidati; `lambda_mult=0.5` dà
    peso uguale a rilevanza e diversità, così file piccoli non vengono
    soffocati da PDF grandi con molti chunk simili tra loro.
    """
    return vs.max_marginal_relevance_search(
        query,
        k=top_k,
        fetch_k=max(top_k * 5, 20),
        lambda_mult=0.5,
    )
