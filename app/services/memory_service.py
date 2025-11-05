"""Business logic for memories."""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Memory
from app.repositories import MemoryRepository
from app.schemas import MemoryCreate, MemoryUpdate
from app.workflows import workflow_engine


class MemoryService:
    """Service handling memory lifecycle."""

    def __init__(self, session: Session):
        self.session = session
        self.repo = MemoryRepository(session)

    def create_memory(self, payload: MemoryCreate) -> Memory:
        ingested_at = datetime.now(timezone.utc)
        recorded_at = payload.captured_at or ingested_at

        context_data = dict(payload.context or {})
        context_data.setdefault("ingested_at", ingested_at.isoformat())

        memory = Memory(
            owner_id=payload.owner_id,
            title=payload.title,
            content=payload.content,
            tags=payload.tags,
            captured_at=recorded_at,
            source_device=payload.source_device,
            source_location=payload.source_location,
            context=context_data,
        )
        memory = self.repo.create(memory)
        workflow_engine.trigger(
            "memory.created",
            session=self.session,
            payload={"memory_id": memory.id},
        )
        return memory

    def get_memory(self, memory_id: uuid.UUID) -> Memory | None:
        return self.repo.get(memory_id)

    def list_memories(self, owner_id: uuid.UUID) -> list[Memory]:
        return self.repo.list_by_owner(owner_id)

    def update_memory(self, memory: Memory, payload: MemoryUpdate) -> Memory:
        if payload.title is not None:
            memory.title = payload.title
        if payload.content is not None:
            memory.content = payload.content
        if payload.tags is not None:
            memory.tags = payload.tags
        if payload.captured_at is not None:
            memory.captured_at = payload.captured_at
        if payload.source_device is not None:
            memory.source_device = payload.source_device
        if payload.source_location is not None:
            memory.source_location = payload.source_location
        if payload.context is not None:
            memory.context = payload.context
        memory.updated_at = datetime.now(timezone.utc)
        memory = self.repo.update(memory)
        workflow_engine.trigger(
            "memory.updated",
            session=self.session,
            payload={"memory_id": memory.id},
        )
        return memory

    def delete_memory(self, memory: Memory) -> None:
        memory_id = memory.id
        self.repo.delete(memory)
        workflow_engine.trigger(
            "memory.deleted",
            session=self.session,
            payload={"memory_id": memory_id},
        )

