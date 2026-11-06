"""Module 4 - Inverted index construction.

term (stem) -> {doc_id: term frequency}. The keys of each inner dict are the
postings list; the values are tf for ranking. `surface` remembers which
original word produced each stem, so wildcard and Soundex search can work
on real words instead of stems.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List

from .analyzer import analyze_pairs


class InvertedIndex:
    def __init__(self) -> None:
        self.term_freq: Dict[str, Dict[int, int]] = defaultdict(dict)
        self.surface: Dict[str, str] = {}      # normalized word -> stem

    def add_text(self, doc_id: int, text: str) -> None:
        for word, stem in analyze_pairs(text):
            self.surface[word] = stem
            counts = self.term_freq[stem]
            counts[doc_id] = counts.get(doc_id, 0) + 1

    def postings(self, stem: str) -> List[int]:
        """Sorted doc ids containing the stem."""
        return sorted(self.term_freq.get(stem, ()))

    def freqs(self, stems: Iterable[str]) -> Dict[int, int]:
        """Combined {doc_id: frequency} over several stems."""
        total: Dict[int, int] = {}
        for s in stems:
            for doc_id, f in self.term_freq.get(s, {}).items():
                total[doc_id] = total.get(doc_id, 0) + f
        return total

    @property
    def vocabulary(self) -> List[str]:
        return sorted(self.term_freq)

    @property
    def surface_words(self) -> List[str]:
        return sorted(self.surface)
