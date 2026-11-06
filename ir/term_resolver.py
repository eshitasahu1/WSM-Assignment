"""Turns one query term into postings, trying in order:

    1. field syntax      doc:5  name:x  author:x  date:x   (parametric index)
                         title:x  body:x                    (zone restriction)
    2. wildcard          comput*  *work  n*k  s?arch       (permuterm index)
    3. exact term        after case folding + stemming
    4. spelling fix      nearest vocabulary term (edit distance <= 2)
    5. Soundex           words that sound alike  (also forced with ~term)

Stopwords resolve to None (ignored by the query processor).
Every fallback adds a human-readable line to `notes`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .normalizer import normalize
from .parametric_index import FIELDS as PARAMETRIC_FIELDS
from .soundex import SoundexIndex, soundex
from .spelling import suggest
from .stemmer import stem
from .stopwords import STOPWORDS
from .wildcard import WildcardIndex


@dataclass
class Resolved:
    postings: Dict[int, int]                     # doc_id -> frequency
    matched: List[str] = field(default_factory=list)  # index terms (stems) that matched
    zone: str = "all"
    explicit_zone: bool = False
    parametric: bool = False


class TermResolver:
    def __init__(self, zone_index, parametric_index) -> None:
        self.zones = zone_index
        self.parametric = parametric_index
        self._wild = {z: WildcardIndex(zone_index[z].surface_words) for z in zone_index.indexes}
        self._soundex = {z: SoundexIndex(zone_index[z].surface_words) for z in zone_index.indexes}

    def resolve(self, raw: str, notes: List[str]) -> Optional[Resolved]:
        zone, explicit = "all", False
        if ":" in raw:
            prefix, _, value = raw.partition(":")
            prefix = prefix.lower()
            if prefix in PARAMETRIC_FIELDS:
                docs = self.parametric.lookup(prefix, value)
                if not docs:
                    notes.append(f"No document matches {prefix}:{value}")
                return Resolved({d: 1 for d in docs}, zone="all", parametric=True)
            if prefix in ("title", "body"):
                zone, explicit, raw = prefix, True, value

        forced_phonetic = raw.startswith("~")
        cleaned = "".join(ch for ch in raw if ch.isalnum() or ch in "*?")
        if not cleaned.strip("*?"):
            return None
        word = normalize(cleaned)
        idx = self.zones[zone]

        if WildcardIndex.is_wildcard(word):
            return self._wildcard(word, raw, zone, explicit, notes)

        if word in STOPWORDS:
            notes.append(f'"{raw}" is a stopword - ignored')
            return None

        term = stem(word)
        if not forced_phonetic:
            if term in idx.term_freq:
                return Resolved(dict(idx.term_freq[term]), [term], zone, explicit)
            fix = suggest(term, idx.vocabulary)
            if fix:
                notes.append(f'Spelling: "{raw}" not found, using "{fix[0]}" (edit distance {fix[1]})')
                return Resolved(idx.freqs([fix[0]]), [fix[0]], zone, explicit)
        return self._phonetic(word, raw, zone, explicit, notes)

    def _wildcard(self, word, raw, zone, explicit, notes) -> Resolved:
        idx = self.zones[zone]
        words = sorted(self._wild[zone].expand(word))
        if not words:
            notes.append(f'Wildcard "{raw}" matched no words in the {zone} zone')
            return Resolved({}, [], zone, explicit)
        stems = sorted({idx.surface[w] for w in words})
        notes.append(f'Wildcard "{raw}" expanded to: {", ".join(words)}')
        return Resolved(idx.freqs(stems), stems, zone, explicit)

    def _phonetic(self, word, raw, zone, explicit, notes) -> Resolved:
        idx = self.zones[zone]
        words = sorted(self._soundex[zone].lookup(word))
        if not words:
            notes.append(f'"{raw}" not found (no spelling or Soundex match)')
            return Resolved({}, [], zone, explicit)
        stems = sorted({idx.surface[w] for w in words})
        notes.append(f'Soundex {soundex(word)}: "{raw}" sounds like {", ".join(words)}')
        return Resolved(idx.freqs(stems), stems, zone, explicit)
