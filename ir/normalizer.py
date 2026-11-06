"""Module 3 - Text normalization / case folding."""
from __future__ import annotations

import unicodedata
from typing import Iterable, List


def normalize(token: str) -> str:
    """Case-fold a token and strip accents (e.g. 'Café' -> 'cafe')."""
    folded = token.casefold()
    decomposed = unicodedata.normalize("NFD", folded)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def normalize_all(tokens: Iterable[str]) -> List[str]:
    return [normalize(t) for t in tokens]
