"""Test preflight.check_ollama: fail fast su Ollama down o modello mancante."""
from __future__ import annotations

import unittest
from unittest.mock import patch

import requests

import preflight


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class PreflightTest(unittest.TestCase):
    def test_ollama_unreachable_exits(self):
        with patch("preflight.requests.get", side_effect=requests.ConnectionError("nope")):
            with self.assertRaises(SystemExit) as cm:
                preflight.check_ollama("http://localhost:11434", "llama3.1:8b", timeout=0.1)
            self.assertNotEqual(cm.exception.code, 0)

    def test_model_missing_exits(self):
        with patch(
            "preflight.requests.get",
            return_value=_Resp({"models": [{"name": "mistral:latest"}]}),
        ):
            with self.assertRaises(SystemExit) as cm:
                preflight.check_ollama("http://localhost:11434", "llama3.1:8b")
            self.assertNotEqual(cm.exception.code, 0)

    def test_model_present_ok(self):
        with patch(
            "preflight.requests.get",
            return_value=_Resp({"models": [{"name": "llama3.1:8b"}]}),
        ):
            # non deve sollevare
            preflight.check_ollama("http://localhost:11434", "llama3.1:8b")

    def test_model_present_with_latest_suffix(self):
        with patch(
            "preflight.requests.get",
            return_value=_Resp({"models": [{"name": "llama3.1:8b:latest"}]}),
        ):
            preflight.check_ollama("http://localhost:11434", "llama3.1:8b")


if __name__ == "__main__":
    unittest.main()
