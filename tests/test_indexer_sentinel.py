"""Test rag/indexer: chunk id determinismo, sentinel config-change detection."""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from langchain_core.documents import Document

from rag.indexer import (
    _chunk_id,
    _load_sentinel,
    _split,
    _write_sentinel,
)


class ChunkIdTest(unittest.TestCase):
    def test_chunk_id_is_deterministic(self):
        a = _chunk_id("f.pdf", "abc", 1, 0)
        b = _chunk_id("f.pdf", "abc", 1, 0)
        self.assertEqual(a, b)

    def test_chunk_id_differs_on_source(self):
        a = _chunk_id("a.pdf", "abc", 1, 0)
        b = _chunk_id("b.pdf", "abc", 1, 0)
        self.assertNotEqual(a, b)

    def test_chunk_id_differs_on_hash(self):
        a = _chunk_id("f.pdf", "abc", 1, 0)
        b = _chunk_id("f.pdf", "xyz", 1, 0)
        self.assertNotEqual(a, b)

    def test_chunk_id_differs_on_index(self):
        a = _chunk_id("f.pdf", "abc", 1, 0)
        b = _chunk_id("f.pdf", "abc", 1, 1)
        self.assertNotEqual(a, b)


class SplitTest(unittest.TestCase):
    def test_split_replaces_none_page_with_minus_one(self):
        d = Document(
            page_content="parola " * 500,
            metadata={"source": "a.md", "page": None, "file_hash": "h"},
        )
        _, metadatas, _ = _split([d], chunk_size=200, chunk_overlap=20)
        self.assertTrue(len(metadatas) >= 1)
        for md in metadatas:
            self.assertEqual(md["page"], -1)

    def test_split_ids_unique_per_chunk(self):
        d = Document(
            page_content="lorem ipsum " * 300,
            metadata={"source": "a.md", "page": None, "file_hash": "h"},
        )
        _, _, ids = _split([d], chunk_size=200, chunk_overlap=20)
        self.assertEqual(len(ids), len(set(ids)))


class SentinelTest(unittest.TestCase):
    def test_write_and_load_roundtrip(self):
        with TemporaryDirectory() as tmp:
            d = Path(tmp) / "chroma"
            cfg = {"embedding_model": "x", "chunk_size": 1000, "chunk_overlap": 150}
            _write_sentinel(d, cfg)
            self.assertEqual(_load_sentinel(d), cfg)

    def test_load_missing_returns_none(self):
        with TemporaryDirectory() as tmp:
            self.assertIsNone(_load_sentinel(Path(tmp)))

    def test_load_corrupt_returns_none(self):
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            d.mkdir(exist_ok=True)
            (d / ".index_config.json").write_text("not-json", encoding="utf-8")
            self.assertIsNone(_load_sentinel(d))


if __name__ == "__main__":
    unittest.main()
