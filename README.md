# WSM Search Engine

Boolean + ranked search engine with wildcards, zones, spelling correction and Soundex, plus a themed tkinter GUI.

```
wsm_search/
├── main.py                  entry point:  python main.py [docs_folder]
├── gui.py                   7. frontend GUI (input box, Search button, read-only results,
│                               Choose Folder / Build Index, Boolean/Ranked switch, dark teal theme)
├── data/                    sample .txt documents (Title / Author / Date header + body)
├── tests/test_engine.py     engine tests (no GUI needed):  python -m unittest discover -s tests
└── ir/
    ├── document_loader.py   1. document loading (+ Title/Author/Date headers)
    ├── tokenizer.py         2. tokenization
    ├── normalizer.py        3. text normalization / case folding
    ├── inverted_index.py    4. inverted index construction (stem -> {doc: tf})
    ├── query_processor.py   5. query processing (AND / OR / NOT, parentheses)
    ├── wildcard.py          6. wildcard processing (permuterm index, * and ?)
    ├── stopwords.py         stopword list
    ├── stemmer.py           suffix-stripping stemmer
    ├── analyzer.py          tokenize -> normalize -> stopwords -> stem
    ├── zone_index.py        title / body / all indexes
    ├── parametric_index.py  doc: name: author: date: fields
    ├── spelling.py          edit-distance spelling correction
    ├── soundex.py           phonetic matching
    ├── term_resolver.py     field -> wildcard -> exact -> spelling -> Soundex
    ├── ranking.py           overlap + tf-idf score accumulation, zone weights
    └── engine.py            glue + highlighted result snippets
```

## Query syntax

| Feature | Examples |
| --- | --- |
| Boolean (case-insensitive operators) | `network AND security`, `cricket OR football`, `comput* NOT network`, `(a OR b) AND c` |
| Wildcards | `comput*`, `*work`, `n*k`, `s?arch` |
| Spelling / Soundex | `netwerk` (corrected), `~sekurity` (sounds like) |
| Zones | `title:network`, `body:network` |
| Fields | `author:iyer`, `date:2006-03`, `doc:5`, `name:cricket` (`doc:` / `name:` alone shows the document) |

Adjacent terms mean AND. Stopwords are ignored. Ranked mode ignores operators and orders by overlap, then accumulated tf x idf score (title hits count double).

Requires Python 3.9+ and tkinter (bundled with the python.org installers; on Debian/Ubuntu: `sudo apt install python3-tk`).
