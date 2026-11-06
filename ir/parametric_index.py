"""Parametric index: exact lookup on structured fields rather than free text.

Fields:  doc:5   name:cricket   author:iyer   date:2006-03
doc is an exact document number; the others are case-insensitive substring matches.
"""
from typing import Set

FIELDS = ("doc", "name", "author", "date")


class ParametricIndex:
    def __init__(self, documents) -> None:
        self._docs = list(documents)

    def lookup(self, field: str, value: str) -> Set[int]:
        v = value.strip().casefold()
        if not v:
            return set()
        if field == "doc":
            return {d.doc_id for d in self._docs if str(d.doc_id) == v}
        return {d.doc_id for d in self._docs if v in getattr(d, field).casefold()}
