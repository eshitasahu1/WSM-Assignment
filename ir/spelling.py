"""Spelling-error correction: nearest vocabulary term by Levenshtein edit distance."""
from typing import Iterable, Optional, Tuple


def levenshtein(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i]
        for j, cb in enumerate(b, start=1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def suggest(term: str, vocabulary: Iterable[str]) -> Optional[Tuple[str, int]]:
    """Return (best_term, distance) or None if nothing is close enough.

    Allowed distance: 1 for 3-letter words, 2 for longer ones, none below that.
    """
    if len(term) < 3:
        return None
    limit = 1 if len(term) == 3 else 2
    best = None
    for candidate in vocabulary:
        if abs(len(candidate) - len(term)) > limit:
            continue
        d = levenshtein(term, candidate)
        if d <= limit and (best is None or d < best[1]):
            best = (candidate, d)
    return best
