"""Interfaccia astratta per i provider LLM."""
from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def chat(self, system: str, user: str) -> str:
        """Invia system + user prompt e ritorna la risposta come stringa."""
        raise NotImplementedError
