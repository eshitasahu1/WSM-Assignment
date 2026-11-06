"""Ranked retrieval: overlap matching + score accumulation + zone weights.

For a free-text query, each term adds  tf * idf  to every document that
contains it (the score is *accumulated* term by term). tf is zone-weighted:
a hit in the Title counts TITLE_WEIGHT times, a hit in the Body BODY_WEIGHT
times (unless the term names a zone, e.g. title:network). Documents are
ordered by overlap (how many distinct query terms they contain) first, then
by accumulated score. AND/OR/NOT/parentheses are ignored in ranked mode.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Set

from .query_processor import OPERATORS, split_query

TITLE_WEIGHT = 2.0
BODY_WEIGHT = 1.0


@dataclass
class RankedDoc:
    doc_id: int
    score: float = 0.0
    terms: Set[str] = field(default_factory=set)
    details: List[tuple] = field(default_factory=list)   # (term, matched, tf, idf, weight)

    @property
    def overlap(self) -> int:
        return len(self.terms)


class Ranker:
    def __init__(self, zone_index, resolver) -> None:
        self.zones = zone_index
        self.resolver = resolver
        self.n_docs = len(zone_index.doc_ids)
        self.matched: Set[str] = set()      # stems of the last query (for highlighting)

    def rank(self, query: str):
        """Return (ranked list of RankedDoc, notes, number of searchable terms)."""
        notes, acc, n_terms = [], {}, 0
        self.matched = set()
        for raw in split_query(query):
            if raw in ("(", ")") or raw in OPERATORS:
                continue
            resolved = self.resolver.resolve(raw, notes)
            if resolved is None:
                continue
            n_terms += 1
            self.matched.update(resolved.matched)
            df = len(resolved.postings)
            if df == 0:
                continue
            idf = math.log((self.n_docs + 1) / (df + 1)) + 1
            for doc_id, freq in resolved.postings.items():
                tf = self._weighted_tf(resolved, doc_id, freq)
                weight = tf * idf
                entry = acc.setdefault(doc_id, RankedDoc(doc_id))
                entry.score += weight                       # score accumulation
                entry.terms.add(raw.lower())
                entry.details.append((raw, ", ".join(resolved.matched) or "(field)", tf, idf, weight))
        ranked = sorted(acc.values(), key=lambda r: (-r.overlap, -r.score, r.doc_id))
        return ranked, notes, n_terms

    def _weighted_tf(self, resolved, doc_id: int, freq: int) -> float:
        if resolved.parametric or resolved.explicit_zone:
            return freq
        title = self.zones["title"].freqs(resolved.matched).get(doc_id, 0)
        body = self.zones["body"].freqs(resolved.matched).get(doc_id, 0)
        return TITLE_WEIGHT * title + BODY_WEIGHT * body
