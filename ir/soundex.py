"""Soundex: phonetic matching for words that sound alike but are spelled differently."""
from collections import defaultdict
from typing import Iterable, List

_CODES = {c: d for d, letters in {"1": "bfpv", "2": "cgjkqsxz", "3": "dt",
                                  "4": "l", "5": "mn", "6": "r"}.items() for c in letters}


def soundex(word: str) -> str:
    word = "".join(ch for ch in word.lower() if ch.isalpha())
    if not word:
        return ""
    result = word[0].upper()
    last = _CODES.get(word[0], "")
    for ch in word[1:]:
        code = _CODES.get(ch, "")
        if code and code != last:
            result += code
        if ch not in "hw":
            last = code
    return (result + "000")[:4]


class SoundexIndex:
    def __init__(self, words: Iterable[str]) -> None:
        self._by_code = defaultdict(list)
        for w in words:
            self._by_code[soundex(w)].append(w)

    def lookup(self, word: str) -> List[str]:
        """Words sharing the Soundex code of `word`."""
        return list(self._by_code.get(soundex(word), ()))
