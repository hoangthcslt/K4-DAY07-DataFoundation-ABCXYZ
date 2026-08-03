from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb

            client = chromadb.Client()
            self._collection = client.get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        metadata = dict(doc.metadata)
        metadata.setdefault("doc_id", doc.id)
        record = {
            "id": f"{doc.id}::{self._next_index}",
            "content": doc.content,
            "metadata": metadata,
            "embedding": [float(value) for value in self._embedding_fn(doc.content)],
        }
        self._next_index += 1
        return record

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if top_k <= 0 or not records:
            return []

        query_embedding = self._embedding_fn(query)
        results = [
            {
                "id": record["id"],
                "content": record["content"],
                "metadata": dict(record["metadata"]),
                "score": float(_dot(query_embedding, record["embedding"])),
            }
            for record in records
        ]
        results.sort(key=lambda result: result["score"], reverse=True)
        return results[:top_k]

    def _all_records(self) -> list[dict[str, Any]]:
        """Read records from the active backend in one normalized format."""
        if not self._use_chroma:
            return list(self._store)

        assert self._collection is not None
        stored = self._collection.get(include=["documents", "metadatas", "embeddings"])
        ids = stored.get("ids") or []
        documents = stored.get("documents") or []
        metadatas = stored.get("metadatas") or []
        embeddings = stored.get("embeddings")
        if embeddings is None:
            embeddings = []
        return [
            {
                "id": record_id,
                "content": content,
                "metadata": metadata or {},
                "embedding": [float(value) for value in embedding],
            }
            for record_id, content, metadata, embedding in zip(
                ids, documents, metadatas, embeddings
            )
        ]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        records = [self._make_record(doc) for doc in docs]
        if not records:
            return

        if self._use_chroma:
            assert self._collection is not None
            self._collection.add(
                ids=[record["id"] for record in records],
                documents=[record["content"] for record in records],
                metadatas=[record["metadata"] for record in records],
                embeddings=[record["embedding"] for record in records],
            )
        else:
            self._store.extend(records)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        return self._search_records(query, self._all_records(), top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma:
            assert self._collection is not None
            return int(self._collection.count())
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        records = self._all_records()
        if metadata_filter:
            records = [
                record
                for record in records
                if all(
                    record["metadata"].get(key) == value
                    for key, value in metadata_filter.items()
                )
            ]
        return self._search_records(query, records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        matching_ids = [
            record["id"]
            for record in self._all_records()
            if record["metadata"].get("doc_id") == doc_id
        ]
        if not matching_ids:
            return False

        if self._use_chroma:
            assert self._collection is not None
            self._collection.delete(ids=matching_ids)
        else:
            matching_id_set = set(matching_ids)
            self._store = [
                record for record in self._store if record["id"] not in matching_id_set
            ]
        return True
