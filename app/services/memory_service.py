"""Business logic for memories."""

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Memory
from app.repositories import MemoryRepository
from app.schemas import MemoryCreate, MemoryUpdate


class MemoryService:
    """Service handling memory lifecycle."""

    def __init__(self, session: Session):
        self.repo = MemoryRepository(session)

    def create_memory(self, payload: MemoryCreate) -> Memory:
        memory = Memory(
            owner_id=payload.owner_id,
            title=payload.title,
            content=payload.content,
            tags=payload.tags,
            captured_at=payload.captured_at,
            source_device=payload.source_device,
            source_location=payload.source_location,
            context=payload.context,
        )
        return self.repo.create(memory)

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
        if payload.source_device is not None:
            memory.source_device = payload.source_device
        if payload.source_location is not None:
            memory.source_location = payload.source_location
        if payload.context is not None:
            memory.context = payload.context
        memory.updated_at = datetime.utcnow()
        return self.repo.update(memory)

    def delete_memory(self, memory: Memory) -> None:
        self.repo.delete(memory)

