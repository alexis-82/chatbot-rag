"""Carica e valida configurazione da .env."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

VALID_PROVIDERS = {"ollama", "anthropic", "openai"}

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").strip().lower()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b").strip()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5").strip()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
).strip()

CHROMA_DIR = Path(os.getenv("CHROMA_DIR", "./chroma_db")).resolve()
DOCS_DIR = Path(os.getenv("DOCS_DIR", "./documents")).resolve()

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
TOP_K = int(os.getenv("TOP_K", "4"))


def validate() -> None:
    """Fail fast se la config è invalida. Chiamare all'avvio."""
    if LLM_PROVIDER not in VALID_PROVIDERS:
        _die(
            f"LLM_PROVIDER='{LLM_PROVIDER}' non valido. "
            f"Valori ammessi: {sorted(VALID_PROVIDERS)}."
        )
    if LLM_PROVIDER == "anthropic" and not ANTHROPIC_API_KEY:
        _die("LLM_PROVIDER=anthropic ma ANTHROPIC_API_KEY è vuota in .env.")
    if LLM_PROVIDER == "openai" and not OPENAI_API_KEY:
        _die("LLM_PROVIDER=openai ma OPENAI_API_KEY è vuota in .env.")
    if not DOCS_DIR.exists():
        _die(f"DOCS_DIR non esiste: {DOCS_DIR}")


def _die(msg: str) -> None:
    print(f"[config] ERRORE: {msg}", file=sys.stderr)
    sys.exit(1)


def active_model_name() -> str:
    return {
        "ollama": OLLAMA_MODEL,
        "anthropic": ANTHROPIC_MODEL,
        "openai": OPENAI_MODEL,
    }[LLM_PROVIDER]
