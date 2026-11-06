"""Checks the document dependency data and the copy of it in the interactive page."""
import json
import re
import unittest
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"


class DocumentDependencies(unittest.TestCase):
    def setUp(self):
        self.graph = json.loads((DOCS / "document-dependencies.json").read_text(encoding="utf-8"))

    def test_edges_are_well_formed(self):
        ids = {n["id"] for n in self.graph["nodes"]}
        for e in self.graph["edges"]:
            self.assertIn(e["from"], ids)
            self.assertIn(e["to"], ids)
            self.assertNotEqual(e["from"], e["to"])
            self.assertIn(e["confidence"], ("documented", "inferred"))
            self.assertTrue(e["evidence"], e)

    def test_page_holds_the_same_data(self):
        html = (DOCS / "document-dependency-graph.html").read_text(encoding="utf-8")
        embedded = re.search(r"^const G=(.*);$", html, re.M).group(1)
        self.assertEqual(json.loads(embedded), self.graph)


if __name__ == "__main__":
    unittest.main()
