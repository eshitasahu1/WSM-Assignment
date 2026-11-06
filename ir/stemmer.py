"""Linguistic module: light suffix-stripping stemmer (Porter-inspired).

Plurals -> derivational suffixes -> ed/ing/er -> trailing 'e', so that
computer / computers / computing / compute share one index term.
It is applied identically to documents and queries.
"""


def stem(word: str) -> str:
    if len(word) <= 3:
        return word
    w = word

    # step 1: plurals
    if w.endswith("sses"):
        w = w[:-2]
    elif w.endswith("ies") and len(w) > 4:
        w = w[:-3] + "y"
    elif w.endswith(("ches", "shes", "xes", "zes")):
        w = w[:-2]
    elif w.endswith("s") and not w.endswith(("ss", "us", "is")):
        w = w[:-1]

    # step 2: derivational suffixes
    for suffix, repl in (("ization", "ize"), ("ational", "ate"), ("fulness", "ful"),
                         ("iveness", "ive"), ("ousness", "ous"), ("ness", ""), ("ment", "")):
        if w.endswith(suffix) and len(w) - len(suffix) + len(repl) >= 3:
            w = w[:-len(suffix)] + repl
            break

    # step 3: ing / ed / er
    for suffix in ("ing", "ed", "er"):
        if w.endswith(suffix) and len(w) - len(suffix) >= 4:
            w = w[:-len(suffix)]
            break

    # step 4: trailing e
    if w.endswith("e") and len(w) > 4:
        w = w[:-1]
    return w
