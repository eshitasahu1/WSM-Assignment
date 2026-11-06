"""Engine tests (no GUI needed):  python -m unittest discover -s tests"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from ir.engine import SearchEngine  # noqa: E402
from ir.soundex import soundex  # noqa: E402
from ir.stemmer import stem  # noqa: E402
from ir.wildcard import WildcardIndex  # noqa: E402


def names(resp):
    return [h.document.name for h in resp.hits]


class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e = SearchEngine(os.path.join(ROOT, "data"))
        cls.e.build_index()

    def test_boolean(self):
        self.assertEqual(names(self.e.search("network AND security")), ["computer_networks.txt"])
        self.assertEqual(names(self.e.search("network or cricket")),
                         ["computer_networks.txt", "cricket_news.txt"])
        self.assertNotIn("cricket_news.txt", names(self.e.search("NOT cricket")))
        self.assertTrue(self.e.search("(index").error)

    def test_case_and_stemming(self):
        self.assertEqual(stem("computers"), stem("computing"))
        self.assertEqual(names(self.e.search("SEARCH")), names(self.e.search("search")))

    def test_wildcards(self):
        r = self.e.search("comput*")
        self.assertGreaterEqual(len(r.hits), 3)
        self.assertEqual(len(self.e.search("s?arch").hits), 3)
        self.assertEqual(WildcardIndex(["search", "sparch", "star"]).expand("s?arch"), ["search", "sparch"])
        self.assertEqual(WildcardIndex(["network", "neck"]).expand("n*k"), ["neck", "network"])

    def test_spelling_and_soundex(self):
        r = self.e.search("netwerk")
        self.assertEqual(names(r), ["computer_networks.txt"])
        self.assertTrue(any("Spelling" in n for n in r.notes))
        self.assertEqual(soundex("security"), soundex("sekurity"))
        self.assertEqual(names(self.e.search("~sekurity")), ["computer_networks.txt"])

    def test_zones_and_fields(self):
        self.assertEqual(names(self.e.search("title:network")), ["computer_networks.txt"])
        self.assertEqual(len(self.e.search("author:iyer").hits), 2)
        self.assertEqual(names(self.e.search("name:cricket")), ["cricket_news.txt"])
        self.assertEqual(self.e.search("doc:2").mode, "documents")

    def test_ranked(self):
        r = self.e.search("computer network", "ranked")
        self.assertEqual(r.hits[0].document.name, "computer_networks.txt")
        self.assertEqual(r.hits[0].overlap, 2)
        self.assertGreater(r.hits[0].score, r.hits[1].score)

    def test_suggested_terms_are_searchable(self):
        terms = self.e.suggested_terms(10)
        self.assertEqual(len(terms), 10)
        for t in terms:
            self.assertTrue(self.e.search(t).hits, t)

    def test_highlights(self):
        h = self.e.search("comput*").hits[0]
        self.assertTrue(h.highlights)
        s, e = h.highlights[0]
        self.assertTrue(h.snippet[s:e].lower().startswith("comput"))


if __name__ == "__main__":
    unittest.main()
