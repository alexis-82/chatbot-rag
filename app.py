"""Entry point del chatbot RAG."""
from __future__ import annotations

import logging
import threading
from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings

import config
import preflight
from llm.factory import get_llm
from rag.indexer import build_or_load_vectorstore, sync_from_disk
from rag.loader import load_documents
from rag.pipeline import answer
from ui.gradio_app import build_ui

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("app")


def _list_indexed_files(chroma_dir: Path) -> list[str]:
    """Ritorna i file attualmente presenti in DOCS_DIR (proxy: cosa dovrebbe essere indicizzato)."""
    docs_dir = config.DOCS_DIR
    return sorted(
        p.name
        for p in docs_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in {".pdf", ".txt", ".md"}
    )


def main() -> None:
    config.validate()

    if config.LLM_PROVIDER == "ollama":
        preflight.check_ollama(config.OLLAMA_BASE_URL, config.OLLAMA_MODEL)

    log.info("Provider LLM: %s (%s)", config.LLM_PROVIDER, config.active_model_name())
    log.info("Embeddings: %s", config.EMBEDDING_MODEL)

    embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)
    vs = build_or_load_vectorstore(
        chroma_dir=config.CHROMA_DIR,
        embedding_function=embeddings,
        embedding_model=config.EMBEDDING_MODEL,
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
    )

    # Prima indicizzazione se l'indice è vuoto
    try:
        count = vs._collection.count()  # noqa: SLF001
    except Exception:
        count = 0
    if count == 0:
        log.info("Indice vuoto: eseguo prima indicizzazione da %s", config.DOCS_DIR)
        docs = load_documents(config.DOCS_DIR)
        if docs:
            from rag.indexer import index_documents

            n = index_documents(vs, docs, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
            log.info("Indicizzati %d chunk", n)
        else:
            log.warning("Nessun documento trovato in %s", config.DOCS_DIR)

    llm = get_llm()
    lock = threading.Lock()

    def chat_fn(query: str):
        with lock:
            return answer(query, vs, llm, config.TOP_K)

    def reindex_fn():
        with lock:
            return sync_from_disk(vs, config.DOCS_DIR, config.CHUNK_SIZE, config.CHUNK_OVERLAP)

    def list_files_fn():
        return _list_indexed_files(config.CHROMA_DIR)

    provider_label = f"{config.LLM_PROVIDER} / {config.active_model_name()}"
    demo = build_ui(chat_fn, reindex_fn, list_files_fn, provider_label)
    demo.queue(default_concurrency_limit=1).launch(server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    main()
