"""Assistant chat schemas."""

import uuid
from typing import Any

from pydantic import BaseModel, Field


class AssistantChatRequest(BaseModel):
    message: str = Field(min_length=1)
    owner_id: uuid.UUID | None = None
    memory_ids: list[uuid.UUID] | None = None
    history: list[dict[str, Any]] | None = None
    top_k: int | None = Field(default=None, ge=1, le=20)
    use_rag: bool = True


class AssistantContextMemory(BaseModel):
    memory_id: uuid.UUID
    title: str
    snippet: str
    score: float | None = None


class AssistantChatResponse(BaseModel):
    reply: str
    used_memory_ids: list[uuid.UUID] = Field(default_factory=list)
    context: list[AssistantContextMemory] = Field(default_factory=list)
