"""Scansione della cartella documenti e parsing PDF/TXT/MD."""
from __future__ import annotations

import codecs
import hashlib
import logging
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

log = logging.getLogger(__name__)

SUPPORTED_EXTS = {".pdf", ".txt", ".md"}
_SNIFF_BYTES = 8192


def _looks_like_text(path: Path) -> bool:
    """True se i primi byte sono UTF-8 valido e senza byte nulli (euristica anti-binario)."""
    with path.open("rb") as f:
        head = f.read(_SNIFF_BYTES)
    if b"\x00" in head:
        return False
    try:
        # se il blocco non è l'intero file, un carattere multibyte troncato in coda non è un errore
        truncated = len(head) == _SNIFF_BYTES
        codecs.getincrementaldecoder("utf-8")().decode(head, final=not truncated)
    except UnicodeDecodeError:
        return False
    return True


def is_supported(path: Path) -> bool:
    """Estensione supportata, oppure file di testo senza estensione (non nascosto)."""
    ext = path.suffix.lower()
    if ext in SUPPORTED_EXTS:
        return True
    if ext or path.name.startswith("."):
        return False
    try:
        return _looks_like_text(path)
    except OSError:
        return False


def _file_sha1(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_pdf(path: Path, file_hash: str) -> list[Document]:
    docs = PyPDFLoader(str(path)).load()
    out: list[Document] = []
    for d in docs:
        text = (d.page_content or "").strip()
        if not text:
            continue
        page_zero = d.metadata.get("page")
        page = (page_zero + 1) if isinstance(page_zero, int) else None
        out.append(
            Document(
                page_content=d.page_content,
                metadata={
                    "source": path.name,
                    "page": page,
                    "file_hash": file_hash,
                },
            )
        )
    if not out:
        log.warning(
            "PDF senza testo estraibile (probabile scansione, OCR fuori scope): %s",
            path.name,
        )
    return out


def _load_text(path: Path, file_hash: str) -> list[Document]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        log.warning("File vuoto: %s", path.name)
        return []
    return [
        Document(
            page_content=text,
            metadata={
                "source": path.name,
                "page": None,
                "file_hash": file_hash,
            },
        )
    ]


def load_documents(docs_dir: Path) -> list[Document]:
    """Scansiona ricorsivamente `docs_dir` e restituisce Document con metadata standard.

    - `source`: nome file (non path assoluto).
    - `page`: 1-indexed per PDF, None per txt/md/senza estensione.
    - `file_hash`: SHA-1 dell'intero file, uniforme su tutti i chunk dello stesso file.
    """
    docs_dir = Path(docs_dir)
    all_docs: list[Document] = []
    for path in sorted(docs_dir.rglob("*")):
        if not path.is_file():
            continue
        if not is_supported(path):
            log.warning("Formato non supportato, ignorato: %s", path.name)
            continue
        file_hash = _file_sha1(path)
        try:
            if path.suffix.lower() == ".pdf":
                all_docs.extend(_load_pdf(path, file_hash))
            else:
                all_docs.extend(_load_text(path, file_hash))
        except Exception as e:
            log.warning("Errore caricamento %s: %s", path.name, e)
    return all_docs
