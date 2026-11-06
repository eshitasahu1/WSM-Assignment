"""Ties the modules together: load -> analyze -> index -> query -> results.

The GUI only talks to this class, so everything is testable without a window.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from .document_loader import Document, load_documents
from .normalizer import normalize
from .parametric_index import ParametricIndex
from .query_processor import QueryError, QueryProcessor, split_query
from .ranking import Ranker
from .stemmer import stem
from .stopwords import STOPWORDS
from .term_resolver import TermResolver
from .tokenizer import iter_tokens, tokenize
from .zone_index import ZoneIndex

SNIPPET_WIDTH = 180


@dataclass
class SearchHit:
    document: Document
    snippet: str
    highlights: List[Tuple[int, int]] = field(default_factory=list)  # offsets in snippet
    overlap: Optional[int] = None          # ranked mode only
    score: Optional[float] = None          # ranked mode only
    details: List[tuple] = field(default_factory=list)  # (term, matched, tf, idf, weight)


@dataclass
class SearchResponse:
    query: str
    mode: str                              # "boolean" | "ranked" | "documents"
    hits: List[SearchHit] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    n_terms: int = 0
    error: str = ""


def make_snippet(text: str, stems: Set[str], width: int = SNIPPET_WIDTH
                 ) -> Tuple[str, List[Tuple[int, int]]]:
    """Short excerpt around the first word whose stem matched, plus highlight spans."""
    flat = re.sub(r"[\r\n\t]", " ", text)  # same length, so offsets stay valid
    spans = []
    for tok, s, e in iter_tokens(flat):
        word = normalize(tok)
        if word not in STOPWORDS and stem(word) in stems:
            spans.append((s, e))
    first = spans[0][0] if spans else 0
    start = max(0, first - width // 3)
    end = min(len(flat), start + width)
    chunk = flat[start:end]
    lead = len(chunk) - len(chunk.lstrip())
    prefix = "… " if start > 0 else ""
    suffix = " …" if end < len(flat) else ""
    snippet = prefix + chunk.strip() + suffix
    shift = len(prefix) - start - lead
    highlights = [(s + shift, e + shift) for s, e in spans if s >= start and e <= end]
    return snippet, highlights


class SearchEngine:
    def __init__(self, folder: Optional[str] = None) -> None:
        self.folder = folder
        self.documents: List[Document] = []
        self._by_id: Dict[int, Document] = {}
        self.zones: Optional[ZoneIndex] = None
        self.processor: Optional[QueryProcessor] = None
        self.ranker: Optional[Ranker] = None

    @property
    def is_ready(self) -> bool:
        return self.processor is not None

    def build_index(self, folder: Optional[str] = None) -> str:
        """The indexer trigger: load the folder, run the pipeline, build all indexes."""
        if folder is not None:
            self.folder = folder
        documents = load_documents(self.folder)
        self.documents = documents
        self._by_id = {d.doc_id: d for d in documents}
        self.zones = ZoneIndex.build(documents)
        resolver = TermResolver(self.zones, ParametricIndex(documents))
        self.processor = QueryProcessor(self.zones, resolver)
        self.ranker = Ranker(self.zones, resolver)
        return self.stats()

    def stats(self) -> str:
        z = self.zones
        return (f"{len(self.documents)} documents | terms: {len(z['all'].vocabulary)} all, "
                f"{len(z['title'].vocabulary)} title, {len(z['body'].vocabulary)} body")

    def suggested_terms(self, n: int = 16) -> List[str]:
        """One topic word per document (its longest title word) - starting points for a search."""
        words: List[str] = []
        for doc in self.documents:
            candidates = [normalize(t) for t in tokenize(doc.title)]
            candidates = [w for w in candidates if w not in STOPWORDS and len(w) >= 4]
            if candidates:
                word = max(candidates, key=len)
                if word not in words:
                    words.append(word)
        if len(words) > n:                       # spread the picks over the whole collection
            words = [words[int(i * len(words) / n)] for i in range(n)]
        return words

    # ---- searching ---------------------------------------------------------
    def search(self, query: str, mode: str = "boolean") -> SearchResponse:
        if not self.is_ready:
            return SearchResponse(query, mode, error='Index not built yet. Click "Build Index" first.')
        tokens = split_query(query)
        if len(tokens) == 1 and tokens[0].lower().startswith(("doc:", "name:")):
            return self._view_documents(query, tokens[0])
        if mode == "ranked":
            return self._ranked(query)
        return self._boolean(query)

    def _hit(self, doc_id: int, stems: Set[str], **extra) -> SearchHit:
        doc = self._by_id[doc_id]
        snippet, highlights = make_snippet(doc.body or doc.text, stems)
        return SearchHit(doc, snippet, highlights, **extra)

    def _boolean(self, query: str) -> SearchResponse:
        try:
            doc_ids = self.processor.search(query)
        except QueryError as err:
            return SearchResponse(query, "boolean", error=f"Query error: {err}")
        stems = self.processor.matched
        hits = [self._hit(i, stems) for i in doc_ids]
        return SearchResponse(query, "boolean", hits, list(dict.fromkeys(self.processor.notes)))

    def _ranked(self, query: str) -> SearchResponse:
        ranked, notes, n_terms = self.ranker.rank(query)
        stems = self.ranker.matched
        hits = [self._hit(r.doc_id, stems, overlap=r.overlap, score=r.score, details=r.details)
                for r in ranked]
        return SearchResponse(query, "ranked", hits, list(dict.fromkeys(notes)), n_terms)

    def _view_documents(self, query: str, token: str) -> SearchResponse:
        notes: List[str] = []
        resolved = self.processor.resolver.resolve(token, notes)
        ids = sorted(resolved.postings)[:3] if resolved else []
        hits = [SearchHit(self._by_id[i], self._by_id[i].body) for i in ids]
        return SearchResponse(query, "documents", hits, list(dict.fromkeys(notes)))
