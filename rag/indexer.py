"""Costruzione, sincronizzazione e persistenza del vector store ChromaDB."""
from __future__ import annotations

import hashlib
import json
import logging
import shutil
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.loader import _file_sha1, load_documents

log = logging.getLogger(__name__)

SENTINEL_NAME = ".index_config.json"
COLLECTION = "docs"


def _sentinel_path(chroma_dir: Path) -> Path:
    return chroma_dir / SENTINEL_NAME


def _load_sentinel(chroma_dir: Path) -> dict | None:
    p = _sentinel_path(chroma_dir)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _write_sentinel(chroma_dir: Path, cfg: dict) -> None:
    chroma_dir.mkdir(parents=True, exist_ok=True)
    _sentinel_path(chroma_dir).write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def build_or_load_vectorstore(
    chroma_dir: Path,
    embedding_function,
    embedding_model: str,
    chunk_size: int,
    chunk_overlap: int,
) -> Chroma:
    """Apre ChromaDB persistente; se la config di indicizzazione è cambiata, ricrea."""
    chroma_dir = Path(chroma_dir)
    current_cfg = {
        "embedding_model": embedding_model,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
    }
    saved = _load_sentinel(chroma_dir)
    if saved is not None and saved != current_cfg:
        log.warning(
            "Config di indicizzazione cambiata (%s -> %s): rigenero l'indice.",
            saved,
            current_cfg,
        )
        shutil.rmtree(chroma_dir, ignore_errors=True)

    chroma_dir.mkdir(parents=True, exist_ok=True)
    vs = Chroma(
        collection_name=COLLECTION,
        embedding_function=embedding_function,
        persist_directory=str(chroma_dir),
    )
    _write_sentinel(chroma_dir, current_cfg)
    return vs


def _chunk_id(source: str, file_hash: str, page, idx: int) -> str:
    key = f"{source}|{file_hash}|{page}|{idx}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()


def _split(documents: list[Document], chunk_size: int, chunk_overlap: int) -> tuple[list[str], list[dict], list[str]]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    texts: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []
    counters: dict[str, int] = {}
    for doc in documents:
        source = doc.metadata.get("source", "?")
        file_hash = doc.metadata.get("file_hash", "?")
        page = doc.metadata.get("page")
        for piece in splitter.split_text(doc.page_content):
            key = f"{source}|{file_hash}|{page}"
            idx = counters.get(key, 0)
            counters[key] = idx + 1
            texts.append(piece)
            # ChromaDB non accetta None nei metadata: sostituiamo con -1
            metadatas.append(
                {
                    "source": source,
                    "page": page if page is not None else -1,
                    "file_hash": file_hash,
                }
            )
            ids.append(_chunk_id(source, file_hash, page, idx))
    return texts, metadatas, ids


def index_documents(
    vs: Chroma,
    documents: list[Document],
    chunk_size: int,
    chunk_overlap: int,
) -> int:
    """Split + upsert idempotente in Chroma. Ritorna il numero di chunk indicizzati."""
    if not documents:
        return 0
    texts, metadatas, ids = _split(documents, chunk_size, chunk_overlap)
    if not texts:
        return 0
    vs.add_texts(texts=texts, metadatas=metadatas, ids=ids)
    return len(texts)


def _indexed_file_hashes(vs: Chroma) -> dict[str, str]:
    """Mappa source -> file_hash come attualmente presente nell'indice."""
    try:
        data = vs.get(include=["metadatas"])
    except Exception as e:
        log.warning("Impossibile leggere metadata da Chroma: %s", e)
        return {}
    result: dict[str, str] = {}
    for md in data.get("metadatas", []) or []:
        if not md:
            continue
        src = md.get("source")
        fh = md.get("file_hash")
        if src and fh:
            result[src] = fh
    return result


def _delete_by_source(vs: Chroma, source: str) -> None:
    try:
        vs.delete(where={"source": source})
    except Exception as e:
        log.warning("Delete chunk di %s fallita: %s", source, e)


def sync_from_disk(
    vs: Chroma,
    docs_dir: Path,
    chunk_size: int,
    chunk_overlap: int,
) -> dict:
    """Allinea l'indice al contenuto di `docs_dir`.

    - Aggiunge file nuovi.
    - Rimuove file cancellati.
    - Aggiorna file il cui contenuto è cambiato (hash diverso).

    Ritorna un piccolo report `{added, removed, updated}`.
    """
    docs_dir = Path(docs_dir)
    on_disk: dict[str, str] = {}
    for path in sorted(docs_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".pdf", ".txt", ".md"}:
            on_disk[path.name] = _file_sha1(path)

    indexed = _indexed_file_hashes(vs)

    to_remove = [src for src in indexed if src not in on_disk]
    to_update = [src for src, h in on_disk.items() if src in indexed and indexed[src] != h]
    to_add = [src for src in on_disk if src not in indexed]

    for src in to_remove + to_update:
        _delete_by_source(vs, src)

    changed = set(to_add + to_update)
    if changed:
        all_docs = load_documents(docs_dir)
        new_docs = [d for d in all_docs if d.metadata.get("source") in changed]
        index_documents(vs, new_docs, chunk_size, chunk_overlap)

    return {"added": len(to_add), "removed": len(to_remove), "updated": len(to_update)}
