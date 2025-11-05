"""Repository for persisted memory embeddings."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MemoryEmbedding


class MemoryEmbeddingRepository:
    """Encapsulates CRUD operations for memory embeddings."""

    def __init__(self, session: Session):
        self.session = session

    def upsert(
        self,
        memory_id: uuid.UUID,
        owner_id: uuid.UUID,
        *,
        embedding_bytes: bytes,
        embedding_dim: int,
        embedding_dtype: str,
        embedding_model: str,
    ) -> MemoryEmbedding:
        record = self.session.get(MemoryEmbedding, memory_id)
        if record:
            record.embedding = embedding_bytes
            record.embedding_dim = embedding_dim
            record.embedding_dtype = embedding_dtype
            record.embedding_model = embedding_model
        else:
            record = MemoryEmbedding(
                memory_id=memory_id,
                owner_id=owner_id,
                embedding=embedding_bytes,
                embedding_dim=embedding_dim,
                embedding_dtype=embedding_dtype,
                embedding_model=embedding_model,
            )
            self.session.add(record)

        self.session.commit()
        self.session.refresh(record)
        return record

    def delete(self, memory_id: uuid.UUID) -> None:
        record = self.session.get(MemoryEmbedding, memory_id)
        if not record:
            return
        self.session.delete(record)
        self.session.commit()

    def get(self, memory_id: uuid.UUID) -> MemoryEmbedding | None:
        return self.session.get(MemoryEmbedding, memory_id)

    def list_by_owner(self, owner_id: uuid.UUID) -> list[MemoryEmbedding]:
        stmt = select(MemoryEmbedding).where(MemoryEmbedding.owner_id == owner_id)
        return list(self.session.scalars(stmt).all())

