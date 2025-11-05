"""Repository for memory entities."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Memory


class MemoryRepository:
    """Encapsulates memory persistence operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, memory: Memory) -> Memory:
        self.session.add(memory)
        self.session.commit()
        self.session.refresh(memory)
        return memory

    def get(self, memory_id: uuid.UUID) -> Memory | None:
        return self.session.get(Memory, memory_id)

    def list_by_owner(self, owner_id: uuid.UUID) -> list[Memory]:
        stmt = (
            select(Memory)
            .where(Memory.owner_id == owner_id)
            .order_by(Memory.created_at.desc())
        )
        return list(self.session.scalars(stmt).all())

    def list_all(self) -> list[Memory]:
        stmt = select(Memory).order_by(Memory.created_at.desc())
        return list(self.session.scalars(stmt).all())

    def update(self, memory: Memory) -> Memory:
        self.session.add(memory)
        self.session.commit()
        self.session.refresh(memory)
        return memory

    def delete(self, memory: Memory) -> None:
        self.session.delete(memory)
        self.session.commit()

