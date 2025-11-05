"""Retrieval-Augmented Generation helpers for MindDock."""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass
from typing import Iterable, Protocol

import numpy as np
from openai import OpenAI
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Memory
from app.repositories import MemoryEmbeddingRepository, MemoryRepository

logger = logging.getLogger(__name__)


class EmbeddingBackend(Protocol):
    """Protocol for embedding providers."""

    name: str

    def embed(self, text: str) -> np.ndarray:
        """Return a vector representation for text."""


class OpenAIEmbeddingBackend:
    """Embedding backend powered by OpenAI's embeddings API."""

    def __init__(self, api_key: str, model_name: str):
        self.name = f"openai::{model_name}"
        self._client = OpenAI(api_key=api_key)
        self._model_name = model_name

    def embed(self, text: str) -> np.ndarray:
        if not text.strip():
            return np.zeros(1, dtype=np.float32)
        response = self._client.embeddings.create(model=self._model_name, input=[text])
        vector = response.data[0].embedding
        return np.asarray(vector, dtype=np.float32)


class LocalHashEmbeddingBackend:
    """Lightweight hashing-based embedding for local fallback."""

    def __init__(self, dim: int = 512):
        self.dim = dim
        self.name = f"local-hash-{dim}"

    @staticmethod
    def _tokenize(text: str) -> Iterable[str]:
        return re.findall(r"\w+", text.lower())

    def embed(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dim, dtype=np.float32)
        tokens = list(self._tokenize(text))
        if not tokens:
            return vector
        for token in tokens:
            index = hash(token) % self.dim
            vector[index] += 1.0
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector /= norm
        return vector


@dataclass
class RAGResult:
    """Result item returned from vector similarity search."""

    memory: Memory
    score: float


class RAGService:
    """Coordinates embedding management and retrieval."""

    def __init__(self, session: Session):
        self.session = session
        self.settings = get_settings()
        self.memory_repo = MemoryRepository(session)
        self.embedding_repo = MemoryEmbeddingRepository(session)
        self._embedder: EmbeddingBackend | None = None

    def _embedder_instance(self) -> EmbeddingBackend:
        if self._embedder is not None:
            return self._embedder

        if not self.settings.rag_enabled:
            raise RuntimeError("RAG is disabled by configuration")

        if self.settings.openai_api_key:
            try:
                self._embedder = OpenAIEmbeddingBackend(
                    api_key=self.settings.openai_api_key,
                    model_name=self.settings.openai_embedding_model,
                )
                logger.info(
                    "RAG using OpenAI embeddings (%s)",
                    self.settings.openai_embedding_model,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Falling back to local embeddings: %s", exc)
                self._embedder = LocalHashEmbeddingBackend(
                    dim=self.settings.rag_local_vector_size
                )
        else:
            self._embedder = LocalHashEmbeddingBackend(
                dim=self.settings.rag_local_vector_size
            )
            logger.info(
                "RAG using local hashing embeddings (dim=%s)",
                self.settings.rag_local_vector_size,
            )

        return self._embedder

    def index_memory(self, memory: Memory) -> None:
        """Add or update a memory's embedding in the vector store."""

        if not self.settings.rag_enabled:
            logger.debug("RAG disabled; skipping index for memory %s", memory.id)
            return

        embedder = self._embedder_instance()
        text = self._compose_memory_text(memory)
        vector = embedder.embed(text)
        if vector.size == 0:
            logger.debug("Empty embedding produced for memory %s", memory.id)
            return

        self.embedding_repo.upsert(
            memory_id=memory.id,
            owner_id=memory.owner_id,
            embedding_bytes=vector.tobytes(),
            embedding_dim=int(vector.shape[0]),
            embedding_dtype=vector.dtype.name,
            embedding_model=embedder.name,
        )

    def delete_memory_embedding(self, memory_id: uuid.UUID) -> None:
        if not self.settings.rag_enabled:
            return
        self.embedding_repo.delete(memory_id)

    def search(  # noqa: C901 complexity acceptable for orchestrator
        self,
        query: str,
        *,
        owner_id: uuid.UUID,
        top_k: int | None = None,
    ) -> list[RAGResult]:
        if not self.settings.rag_enabled:
            return []

        records = self.embedding_repo.list_by_owner(owner_id)
        if not records:
            return []

        embedder = self._embedder_instance()
        query_vector = embedder.embed(query)
        if query_vector.size == 0:
            return []

        query_norm = np.linalg.norm(query_vector)
        if query_norm == 0:
            return []

        scored_ids: list[tuple[uuid.UUID, float]] = []
        for record in records:
            vector = np.frombuffer(
                record.embedding,
                dtype=np.dtype(record.embedding_dtype),
            )
            if vector.size == 0:
                continue
            vector_norm = np.linalg.norm(vector)
            if vector_norm == 0:
                continue
            score = float(np.dot(query_vector, vector) / (query_norm * vector_norm))
            scored_ids.append((record.memory_id, score))

        scored_ids.sort(key=lambda item: item[1], reverse=True)
        limit = top_k or self.settings.rag_default_top_k
        selected = scored_ids[:limit]

        results: list[RAGResult] = []
        for memory_id, score in selected:
            memory = self.memory_repo.get(memory_id)
            if memory is None:
                continue
            results.append(RAGResult(memory=memory, score=score))

        return results

    @staticmethod
    def _compose_memory_text(memory: Memory) -> str:
        parts = [memory.title or "", memory.content or ""]
        if memory.tags:
            parts.append("Tags: " + ", ".join(memory.tags))
        if memory.context:
            parts.append(f"Context: {memory.context}")
        return "\n\n".join(part for part in parts if part)

