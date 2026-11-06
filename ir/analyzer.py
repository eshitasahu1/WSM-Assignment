"""Linguistic pipeline: tokenize -> normalize -> remove stopwords -> stem.

Used for every document zone, so index terms are always produced the same way.
"""
from typing import Iterator, List, Tuple

from .normalizer import normalize
from .stemmer import stem
from .stopwords import STOPWORDS
from .tokenizer import tokenize


def analyze_pairs(text: str) -> Iterator[Tuple[str, str]]:
    """Yield (normalized word, stem) for every non-stopword token."""
    for token in tokenize(text):
        word = normalize(token)
        if word not in STOPWORDS:
            yield word, stem(word)


def analyze(text: str) -> List[str]:
    return [s for _, s in analyze_pairs(text)]
