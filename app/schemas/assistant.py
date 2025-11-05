"""Assistant chat schemas."""

import uuid
from typing import Any

from pydantic import BaseModel, Field


class AssistantChatRequest(BaseModel):
    message: str = Field(min_length=1)
    memory_ids: list[uuid.UUID] | None = None
    history: list[dict[str, Any]] | None = None


class AssistantChatResponse(BaseModel):
    reply: str
    used_memory_ids: list[uuid.UUID] = []
