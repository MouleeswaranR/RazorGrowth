import os
import logging
from typing import Any
import chromadb
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class VectorMemoryService:
    """Manages persistent vector embeddings and similarity retrieval for historical sessions and campaign outcomes."""

    def __init__(self, storage_path: str = "./data/vector_memory") -> None:
        """Initializes persistent ChromaDB client and session collection."""
        os.makedirs(storage_path, exist_ok=True)
        self._client = chromadb.PersistentClient(path=storage_path)
        self._collection = self._client.get_or_create_collection(name="session_memory")

    def store_memory(
        self,
        memory_id: str,
        merchant_id: str,
        memory_type: str,
        summary_text: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Persists embedded episodic memory record for a merchant."""
        meta = {**(metadata or {}), "merchant_id": merchant_id, "memory_type": memory_type}
        # Clean metadata values to ensure primitive compatibility
        safe_meta = {
            k: (str(v) if isinstance(v, (list, dict)) else v)
            for k, v in meta.items()
            if v is not None
        }

        embedding = embedding_service.embed_text(summary_text)
        try:
            self._collection.upsert(
                ids=[memory_id],
                embeddings=[embedding],
                documents=[summary_text],
                metadatas=[safe_meta],
            )
        except Exception as err:
            logger.warning(f"Vector memory storage failed for {memory_id}: {err}")

    def find_similar_memories(
        self,
        merchant_id: str,
        query_text: str,
        top_k: int = 3,
        strict_merchant: bool = True,
    ) -> list[dict[str, Any]]:
        """Retrieves top-k semantically relevant past episodic memories for a merchant.

        When ``strict_merchant`` is True (default), results are confined to the given
        ``merchant_id``; if that merchant has no memories yet, an empty list is returned
        rather than leaking another merchant's campaign history. Set ``strict_merchant``
        to False only for intentionally cross-merchant/cross-session comparisons.
        """
        total_count = self._collection.count()
        if total_count == 0:
            return []

        query_vec = embedding_service.embed_text(query_text)
        n_results = max(1, min(top_k, total_count))

        if merchant_id:
            try:
                results = self._collection.query(
                    query_embeddings=[query_vec],
                    n_results=n_results,
                    where={"merchant_id": merchant_id},
                )
                docs = results.get("documents", [[]])[0]
                if docs and len(docs) > 0:
                    metas = results.get("metadatas", [[]])[0]
                    ids = results.get("ids", [[]])[0]
                    return [
                        {
                            "id": ids[idx],
                            "summary": docs[idx],
                            "metadata": metas[idx] if idx < len(metas) else {},
                        }
                        for idx in range(len(docs))
                    ]
            except Exception:
                pass

            # No memories for this specific merchant. Do not leak other merchants'
            # history into a per-merchant scan unless explicitly allowed.
            if strict_merchant:
                return []

        try:
            results = self._collection.query(
                query_embeddings=[query_vec],
                n_results=n_results,
            )
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            ids = results.get("ids", [[]])[0]

            return [
                {
                    "id": ids[idx],
                    "summary": docs[idx],
                    "metadata": metas[idx] if idx < len(metas) else {},
                }
                for idx in range(len(docs))
            ]
        except Exception as err:
            logger.warning(f"Vector memory retrieval failed for query '{query_text}': {err}")
            return []


vector_memory_service = VectorMemoryService()
