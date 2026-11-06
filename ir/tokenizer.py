"""Module 2 - Tokenization.

Splits raw text into tokens. Two flavours:
  * tokenize()        - for documents: runs of letters/digits.
  * tokenize_query()  - for queries: additionally keeps parentheses and the
                        wildcard characters '*' and '?' as part of terms.
"""
from __future__ import annotations

import re
from typing import Iterator, List, Tuple

_DOC_TOKEN = re.compile(r"[^\W_]+", re.UNICODE)
# Query tokens: parentheses, or any run without spaces/parentheses. This keeps
# field syntax (author:iyer), wildcards (comput*, s?arch) and ~soundex intact.
_QUERY_TOKEN = re.compile(r"\(|\)|[^\s()]+")


def iter_tokens(text: str) -> Iterator[Tuple[str, int, int]]:
    """Yield (token, start, end) for each document token (used for highlighting)."""
    for m in _DOC_TOKEN.finditer(text):
        yield m.group(), m.start(), m.end()


def tokenize(text: str) -> List[str]:
    """Split document text into raw (not yet normalized) tokens."""
    return _DOC_TOKEN.findall(text)


def tokenize_query(query: str) -> List[str]:
    """Split a query string into tokens, keeping '(' ')' and wildcard terms."""
    return _QUERY_TOKEN.findall(query)
