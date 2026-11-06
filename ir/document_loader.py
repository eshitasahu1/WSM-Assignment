"""Module 1 - Document loading.

Reads every .txt/.md file in a folder. If a file starts with the three header
lines  Title: / Author: / Date:  they become separate fields (the Title zone
and the parametric fields); everything after is the Body zone. Files without
headers are still loaded: title = file name, author = Unknown, date = N/A.
Document ids are 1..N in sorted file-name order.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

SUPPORTED_EXTENSIONS = (".txt", ".md")
_HEADER_RE = [re.compile(rf"^{k}:\s*(.*)$", re.I) for k in ("title", "author", "date")]


@dataclass
class Document:
    doc_id: int
    name: str
    path: str
    title: str
    author: str
    date: str
    body: str
    text: str            # the full raw file content


def parse_document(doc_id: int, name: str, path: str, text: str) -> Document:
    lines = text.splitlines()
    matches = [_HEADER_RE[i].match(lines[i]) if i < len(lines) else None for i in range(3)]
    if all(matches):
        title, author, date = (m.group(1).strip() for m in matches)
        body = " ".join(lines[3:]).strip()
    else:
        title, author, date = Path(name).stem.replace("_", " "), "Unknown", "N/A"
        body = " ".join(lines).strip()
    return Document(doc_id, name, path, title, author, date, body, text)


def load_documents(folder: str) -> List[Document]:
    folder_path = Path(folder)
    if not folder_path.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder}")

    files = sorted(p for p in folder_path.iterdir()
                   if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS)
    documents = [
        parse_document(i, p.name, str(p), p.read_text(encoding="utf-8", errors="replace"))
        for i, p in enumerate(files, start=1)
    ]
    if not documents:
        raise ValueError(f"No .txt files found in {folder}")
    return documents
