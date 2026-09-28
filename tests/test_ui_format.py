"""Test ui/gradio_app._format_sources: page 1-indexed per PDF, omesso per md/txt."""
from __future__ import annotations

import unittest

from ui.gradio_app import _format_sources


class FormatSourcesTest(unittest.TestCase):
    def test_empty_returns_empty_string(self):
        self.assertEqual(_format_sources([]), "")

    def test_pdf_source_shows_page(self):
        out = _format_sources([{"source": "lenovo_t470.pdf", "page": 1}])
        self.assertIn("lenovo_t470.pdf p.1", out)
        self.assertNotIn("p.0", out)

    def test_md_source_hides_page(self):
        out = _format_sources([{"source": "note.md", "page": None}])
        self.assertIn("note.md", out)
        self.assertNotIn("p.", out)

    def test_mixed_sources(self):
        out = _format_sources(
            [
                {"source": "a.pdf", "page": 3},
                {"source": "b.md", "page": None},
            ]
        )
        self.assertIn("a.pdf p.3", out)
        self.assertIn("b.md", out)


if __name__ == "__main__":
    unittest.main()
