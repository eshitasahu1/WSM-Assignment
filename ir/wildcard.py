"""Module 6 - Wildcard processing (permuterm index).

Supports '*' (any run of characters) and '?' (exactly one character).

Every vocabulary term t is stored as all rotations of t + '$'. A wildcard
query is rotated so its first '*' ends up at the end, which turns it into a
prefix lookup (binary search). Queries with several wildcards are then
verified with a regular expression.
"""
from __future__ import annotations

import bisect
import re
from typing import Iterable, List, Tuple

END = "$"


class WildcardIndex:
    def __init__(self, vocabulary: Iterable[str]) -> None:
        entries: List[Tuple[str, str]] = []
        for term in vocabulary:
            padded = term + END
            for i in range(len(padded)):
                entries.append((padded[i:] + padded[:i], term))
        entries.sort()
        self._keys = [k for k, _ in entries]
        self._terms = [t for _, t in entries]

    @staticmethod
    def is_wildcard(token: str) -> bool:
        return "*" in token or "?" in token

    def expand(self, pattern: str) -> List[str]:
        """Return all vocabulary terms matching `pattern` (already normalized)."""
        if not self.is_wildcard(pattern):
            return [pattern] if self._exists(pattern) else []

        regex = re.compile(
            "^" + "".join(".*" if c == "*" else "." if c == "?" else re.escape(c)
                          for c in pattern) + "$"
        )
        prefix = self._permuterm_prefix(pattern)
        lo = bisect.bisect_left(self._keys, prefix)
        hi = bisect.bisect_left(self._keys, prefix + "\U0010ffff")
        candidates = set(self._terms[lo:hi])
        return sorted(t for t in candidates if regex.match(t))

    def _exists(self, term: str) -> bool:
        key = term + END
        i = bisect.bisect_left(self._keys, key)
        return i < len(self._keys) and self._keys[i] == key

    @staticmethod
    def _permuterm_prefix(pattern: str) -> str:
        """Rotate pattern+'$' so the text after the last '*'/'?' run leads,
        giving the longest fixed prefix to binary-search on."""
        padded = pattern + END
        # position of the first wildcard char
        first = min(i for i, c in enumerate(padded) if c in "*?")
        rotated = padded[first + 1:] + padded[:first]
        # cut at the next wildcard: remaining wildcards are checked by regex
        for i, c in enumerate(rotated):
            if c in "*?":
                return rotated[:i]
        return rotated
