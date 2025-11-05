"""Attachment schema definitions."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class AttachmentCreate(BaseModel):
    memory_id: uuid.UUID


class AttachmentRead(BaseModel):
    id: uuid.UUID
    filename: str
    content_type: str | None
    size_bytes: int | None
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }

