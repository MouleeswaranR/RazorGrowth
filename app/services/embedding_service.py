import logging
from typing import Sequence

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generates dense semantic vector embeddings using local in-process ONNX models."""

    def __init__(self) -> None:
        """Initializes the fast local embedding model with fallback support."""
        self._embedder = None
        self._dimension = 384
        try:
            from fastembed import TextEmbedding
            self._embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        except Exception as err:
            logger.warning(f"FastEmbed initialization deferred: {err}")

    def embed_text(self, text: str) -> list[float]:
        """Encodes single text string into a normalized 384-dimensional dense vector."""
        if not text or not text.strip():
            return [0.0] * self._dimension

        if self._embedder is not None:
            try:
                embeddings = list(self._embedder.embed([text]))
                if embeddings and len(embeddings) > 0:
                    return [float(val) for val in embeddings[0]]
            except Exception as err:
                logger.warning(f"FastEmbed encoding failed, falling back: {err}")

        # Deterministic semantic hash projection fallback
        return self._generate_deterministic_fallback(text)

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Encodes batch of text strings into normalized dense vector representations."""
        return [self.embed_text(t) for t in texts]

    def _generate_deterministic_fallback(self, text: str) -> list[float]:
        """Produces a deterministic normalized vector fallback based on text token hashing."""
        import hashlib
        import math

        vector = [0.0] * self._dimension
        tokens = text.lower().split()
        for idx, token in enumerate(tokens):
            digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
            pos = int(digest[:8], 16) % self._dimension
            weight = 1.0 / (idx + 1.0)
            vector[pos] += weight

        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            return [x / norm for x in vector]
        return [1.0 / math.sqrt(self._dimension)] * self._dimension


embedding_service = EmbeddingService()
