"""Memory schema definitions."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.attachment import AttachmentRead


class MemoryBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str
    tags: list[str] | None = None
    captured_at: datetime | None = None
    source_device: str | None = Field(default=None, max_length=100)
    source_location: str | None = Field(default=None, max_length=255)
    context: dict | None = None


class MemoryCreate(MemoryBase):
    owner_id: uuid.UUID


class MemoryUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = None
    tags: list[str] | None = None
    captured_at: datetime | None = None
    source_device: str | None = Field(default=None, max_length=100)
    source_location: str | None = Field(default=None, max_length=255)
    context: dict | None = None


class MemoryRead(MemoryBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class MemoryReadWithAttachments(MemoryRead):
    attachments: list[AttachmentRead]

