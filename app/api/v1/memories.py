"""Memory API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas import MemoryCreate, MemoryRead, MemoryReadWithAttachments, MemoryUpdate
from app.services import MemoryService


router = APIRouter()


@router.post("/", response_model=MemoryRead, status_code=status.HTTP_201_CREATED)
def create_memory(
    payload: MemoryCreate,
    db: Session = Depends(deps.get_db),
) -> MemoryRead:
    """Create a new memory entry."""

    service = MemoryService(db)
    memory = service.create_memory(payload)
    return MemoryRead.model_validate(memory)


@router.get("/", response_model=list[MemoryRead])
def list_memories(
    owner_id: uuid.UUID = Query(..., description="Owner identifier"),
    db: Session = Depends(deps.get_db),
) -> list[MemoryRead]:
    """List memories for a specific owner."""

    service = MemoryService(db)
    memories = service.list_memories(owner_id)
    return [MemoryRead.model_validate(memory) for memory in memories]


@router.get("/{memory_id}", response_model=MemoryReadWithAttachments)
def read_memory(memory_id: uuid.UUID, db: Session = Depends(deps.get_db)) -> MemoryReadWithAttachments:
    """Retrieve a memory and its attachments."""

    service = MemoryService(db)
    memory = service.get_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return MemoryReadWithAttachments.model_validate(memory)


@router.patch("/{memory_id}", response_model=MemoryRead)
def update_memory(
    memory_id: uuid.UUID,
    payload: MemoryUpdate,
    db: Session = Depends(deps.get_db),
) -> MemoryRead:
    """Update an existing memory."""

    service = MemoryService(db)
    memory = service.get_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    updated = service.update_memory(memory, payload)
    return MemoryRead.model_validate(updated)


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory(memory_id: uuid.UUID, db: Session = Depends(deps.get_db)) -> None:
    """Delete a memory."""

    service = MemoryService(db)
    memory = service.get_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    service.delete_memory(memory)

