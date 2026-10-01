from __future__ import annotations

import os
from typing import Any

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class EmbeddingService:
    """Generate and persist NEXO taxonomy embeddings.

    Uses the same embedding model for taxonomy documents and query terms. The
    vectors are retrieval signals only; human validation remains mandatory.
    """

    def __init__(self, repo, api_key: str | None = None, model: str | None = None):
        self.repo = repo
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        if self.api_key and OpenAI is None:
            raise RuntimeError("Pacote openai não instalado. Execute pip install -r requirements.txt.")
        self.client = OpenAI(api_key=self.api_key) if (self.api_key and OpenAI is not None) else None

    @property
    def enabled(self) -> bool:
        return bool(self.client and getattr(self.repo, "is_persistent", False))

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not self.client:
            raise RuntimeError("OPENAI_API_KEY não configurada para embeddings.")
        if not texts:
            return []
        response = self.client.embeddings.create(model=self.model, input=texts)
        ordered = sorted(response.data, key=lambda x: x.index)
        return [row.embedding for row in ordered]

    def ensure_taxonomy_index(self, batch_size: int = 64) -> dict[str, int]:
        """Generate only missing/outdated vectors for canonical names + aliases."""
        if not self.enabled:
            return {"indexed": 0, "pending": 0}
        docs = self.repo.get_embedding_documents(self.model, only_missing=True)
        if docs.empty:
            return {"indexed": 0, "pending": 0}

        indexed = 0
        records = docs.to_dict("records")
        for i in range(0, len(records), batch_size):
            chunk = records[i:i + batch_size]
            vectors = self.embed([r["content"] for r in chunk])
            payload = []
            for row, vector in zip(chunk, vectors):
                payload.append({
                    "embedding_id": str(row["embedding_id"]),
                    "embedding_model": self.model,
                    "embedding": vector,
                })
            self.repo.update_skill_embeddings(payload)
            indexed += len(payload)
        return {"indexed": indexed, "pending": max(0, len(records) - indexed)}

    def semantic_candidates(self, term: str, threshold: float = 0.45, count: int = 3) -> list[dict[str, Any]]:
        if not self.enabled:
            return []
        # Ensure taxonomy is populated lazily before first semantic query.
        self.ensure_taxonomy_index()
        vector = self.embed([term])[0]
        return self.repo.semantic_skill_search(vector, threshold=threshold, count=count, embedding_model=self.model)
