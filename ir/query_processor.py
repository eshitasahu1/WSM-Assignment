"""Module 5 - Query processing (Boolean retrieval).

AND, OR, NOT and parentheses. Precedence: NOT > AND > OR. Two terms side by
side mean AND. Operators are case-insensitive. Each term is resolved by the
TermResolver (wildcards, fields, spelling, Soundex). Stopwords are ignored,
so "history of india" works like "history india".

Grammar:
    or_expr  := and_expr ( OR and_expr )*
    and_expr := not_expr ( [AND] not_expr )*
    not_expr := NOT not_expr | primary
    primary  := '(' or_expr ')' | term
"""
from __future__ import annotations

from typing import List, Optional, Set

from .tokenizer import tokenize_query

OPERATORS = {"AND", "OR", "NOT"}


class QueryError(ValueError):
    pass


def split_query(query: str) -> List[str]:
    """Query string -> tokens, with AND/OR/NOT upper-cased."""
    return [t.upper() if t.upper() in OPERATORS else t for t in tokenize_query(query)]


def _and(a: Optional[Set[int]], b: Optional[Set[int]]) -> Optional[Set[int]]:
    return b if a is None else a if b is None else a & b


def _or(a: Optional[Set[int]], b: Optional[Set[int]]) -> Optional[Set[int]]:
    return b if a is None else a if b is None else a | b


class QueryProcessor:
    def __init__(self, zone_index, resolver) -> None:
        self.all_docs = set(zone_index.doc_ids)
        self.resolver = resolver
        self.notes: List[str] = []
        self.matched: Set[str] = set()   # stems matched by non-negated terms (for highlighting)
        self._tokens: List[str] = []
        self._pos = 0
        self._negated = 0

    def search(self, query: str) -> List[int]:
        """Sorted list of matching doc ids. Fallback messages go to self.notes."""
        self.notes = []
        self.matched = set()
        self._tokens = split_query(query)
        self._pos = 0
        self._negated = 0
        if not self._tokens:
            raise QueryError("Empty query.")
        result = self._parse_or()
        if self._pos != len(self._tokens):
            raise QueryError(f"Unexpected '{self._tokens[self._pos]}' in query.")
        if result is None:
            self.notes.append("Nothing searchable in the query (only stopwords/symbols).")
            return []
        return sorted(result)

    def _peek(self) -> Optional[str]:
        return self._tokens[self._pos] if self._pos < len(self._tokens) else None

    def _next(self) -> Optional[str]:
        tok = self._peek()
        self._pos += 1
        return tok

    def _parse_or(self):
        result = self._parse_and()
        while self._peek() == "OR":
            self._next()
            result = _or(result, self._parse_and())
        return result

    def _parse_and(self):
        result = self._parse_not()
        while True:
            tok = self._peek()
            if tok == "AND":
                self._next()
                result = _and(result, self._parse_not())
            elif tok is not None and tok not in ("OR", ")"):
                result = _and(result, self._parse_not())        # implicit AND
            else:
                return result

    def _parse_not(self):
        if self._peek() == "NOT":
            self._next()
            self._negated += 1
            inner = self._parse_not()
            self._negated -= 1
            return None if inner is None else self.all_docs - inner
        return self._parse_primary()

    def _parse_primary(self):
        tok = self._next()
        if tok is None:
            raise QueryError("Query ended unexpectedly.")
        if tok == "(":
            result = self._parse_or()
            if self._next() != ")":
                raise QueryError("Missing closing parenthesis.")
            return result
        if tok in (")", "AND", "OR"):
            raise QueryError(f"Unexpected '{tok}' in query.")
        resolved = self.resolver.resolve(tok, self.notes)
        if resolved is None:
            return None
        if not self._negated:
            self.matched.update(resolved.matched)
        return set(resolved.postings)
