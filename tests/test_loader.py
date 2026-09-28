"""Test rag/loader: file_hash uniforme, page 1-indexed, formati supportati."""
from __future__ import annotations

import logging
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from rag.loader import _file_sha1, load_documents


class LoaderTest(unittest.TestCase):
    def test_txt_load_and_metadata(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "note.txt").write_text("ciao mondo", encoding="utf-8")
            docs = load_documents(root)
            self.assertEqual(len(docs), 1)
            self.assertEqual(docs[0].metadata["source"], "note.txt")
            self.assertIsNone(docs[0].metadata["page"])
            self.assertEqual(len(docs[0].metadata["file_hash"]), 40)  # sha1 hex

    def test_md_load(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "doc.md").write_text("# Titolo\n\ntesto", encoding="utf-8")
            docs = load_documents(root)
            self.assertEqual(len(docs), 1)
            self.assertEqual(docs[0].metadata["source"], "doc.md")

    def test_unsupported_extension_ignored_with_warning(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "foo.docx").write_bytes(b"binary")
            (root / "ok.txt").write_text("ok", encoding="utf-8")
            with self.assertLogs("rag.loader", level="WARNING") as cm:
                docs = load_documents(root)
            self.assertEqual(len(docs), 1)
            self.assertEqual(docs[0].metadata["source"], "ok.txt")
            self.assertTrue(any("foo.docx" in m for m in cm.output))

    def test_empty_txt_logs_warning(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "empty.txt").write_text("", encoding="utf-8")
            with self.assertLogs("rag.loader", level="WARNING") as cm:
                docs = load_documents(root)
            self.assertEqual(docs, [])
            self.assertTrue(any("empty.txt" in m for m in cm.output))

    def test_file_hash_is_content_hash(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "a.txt"
            b = root / "b.txt"
            a.write_text("uguale", encoding="utf-8")
            b.write_text("uguale", encoding="utf-8")
            self.assertEqual(_file_sha1(a), _file_sha1(b))
            b.write_text("diverso", encoding="utf-8")
            self.assertNotEqual(_file_sha1(a), _file_sha1(b))

    def test_pdf_page_is_one_indexed_and_hash_uniform(self):
        """Verifica sui PDF reali che page parta da 1 e file_hash sia uniforme."""
        pdf_dir = Path(__file__).resolve().parent.parent / "documents"
        if not pdf_dir.exists() or not any(pdf_dir.glob("*.pdf")):
            self.skipTest("Nessun PDF di esempio in documents/")
        try:
            docs = load_documents(pdf_dir)
        except Exception as e:
            self.skipTest(f"pypdf non installato o errore parsing: {e}")
        if not docs:
            self.skipTest("PDF senza testo estraibile")
        pages = [d.metadata["page"] for d in docs if d.metadata["source"].endswith(".pdf")]
        self.assertTrue(all(isinstance(p, int) and p >= 1 for p in pages))
        # file_hash uniforme per stesso source
        by_source: dict[str, set[str]] = {}
        for d in docs:
            by_source.setdefault(d.metadata["source"], set()).add(d.metadata["file_hash"])
        for src, hashes in by_source.items():
            self.assertEqual(len(hashes), 1, f"file_hash non uniforme per {src}: {hashes}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    unittest.main()
