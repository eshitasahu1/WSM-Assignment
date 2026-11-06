"""Zone indexes: a separate inverted index for the Title zone, the Body
zone, and one over both ('all'). Queries like  title:network  search a
single zone; plain terms search 'all'.
"""
from .inverted_index import InvertedIndex

ZONES = ("title", "body", "all")


class ZoneIndex:
    def __init__(self) -> None:
        self.indexes = {z: InvertedIndex() for z in ZONES}
        self.doc_ids = set()

    @classmethod
    def build(cls, documents) -> "ZoneIndex":
        zi = cls()
        for doc in documents:
            zi.doc_ids.add(doc.doc_id)
            zi.indexes["title"].add_text(doc.doc_id, doc.title)
            zi.indexes["body"].add_text(doc.doc_id, doc.body)
            zi.indexes["all"].add_text(doc.doc_id, doc.title + " " + doc.body)
        return zi

    def __getitem__(self, zone: str) -> InvertedIndex:
        return self.indexes[zone]
