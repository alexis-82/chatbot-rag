"""Health-check di prerequisiti runtime (Ollama)."""
from __future__ import annotations

import sys

import requests


def check_ollama(base_url: str, model: str, timeout: float = 3.0) -> None:
    """Verifica che Ollama risponda e che `model` sia scaricato.

    Esce con exit code 2 se il check fallisce, con messaggio umano.
    """
    url = f"{base_url.rstrip('/')}/api/tags"
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as e:
        _die(
            f"Ollama non raggiungibile su {base_url}: {e}. "
            f"Avvia il servizio (`ollama serve`) o correggi OLLAMA_BASE_URL in .env."
        )
        return

    data = resp.json()
    available = {m.get("name", "") for m in data.get("models", [])}
    if model not in available and f"{model}:latest" not in available:
        _die(
            f"Modello Ollama '{model}' non trovato. "
            f"Esegui: `ollama pull {model}`. "
            f"Modelli disponibili: {sorted(available) or '(nessuno)'}."
        )


def _die(msg: str) -> None:
    print(f"[preflight] ERRORE: {msg}", file=sys.stderr)
    sys.exit(2)
