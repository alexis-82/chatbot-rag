from __future__ import annotations

import re
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document


def _indexed_sources(vs: Chroma) -> list[str]:
    """Elenco distinto dei `source` presenti nell'indice (nomi file)."""
    try:
        data = vs.get(include=["metadatas"])
        seen = {m.get("source") for m in data.get("metadatas", []) if m}
        return [s for s in seen if s]
    except Exception:
        return []


def _match_source_in_query(query: str, sources: list[str]) -> str | None:
    """Se nella query compare il nome (anche senza estensione) di un file
    indicizzato, restituisce il `source` corrispondente. Match case-insensitive
    sulla parola intera. In caso di ambiguità vince il match più lungo.
    """
    q = query.lower()
    best: tuple[int, str] | None = None
    for src in sources:
        stem = Path(src).stem.lower()
        full = src.lower()
        for needle in (full, stem):
            if not needle or len(needle) < 3:
                continue
            if re.search(rf"\b{re.escape(needle)}\b", q):
                if best is None or len(needle) > best[0]:
                    best = (len(needle), src)
    return best[1] if best else None


def retrieve(vs: Chroma, query: str, top_k: int) -> list[Document]:
    """Retrieval ibrido.

    1. Se la query nomina esplicitamente un file indicizzato, 
       restituisce i top-K chunk di QUEL file ordinati per
       similarità → le query "meta" sul nome del file funzionano.
    2. Altrimenti usa MMR (similarità + diversità delle fonti), così file
       piccoli non vengono soffocati da PDF grandi con molti chunk simili.
    """
    target = _match_source_in_query(query, _indexed_sources(vs))
    if target:
        return vs.similarity_search(query, k=top_k, filter={"source": target})

    return vs.max_marginal_relevance_search(
        query,
        k=top_k,
        fetch_k=max(top_k * 5, 20),
        lambda_mult=0.5,
    )
