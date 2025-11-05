"""Default workflow registrations for MindDock."""

from __future__ import annotations

import logging
import uuid

from app.repositories import MemoryRepository
from app.services.rag_service import RAGService

from .engine import Workflow, WorkflowContext, WorkflowEngine

logger = logging.getLogger(__name__)


def _extract_memory_id(context: WorkflowContext) -> uuid.UUID | None:
    raw_id = context.payload.get("memory_id")
    if raw_id is None:
        logger.debug("Workflow payload missing memory_id")
        return None
    if isinstance(raw_id, uuid.UUID):
        return raw_id
    try:
        return uuid.UUID(str(raw_id))
    except (ValueError, TypeError):
        logger.warning("Invalid memory_id in workflow payload: %s", raw_id)
        return None


def _index_memory_step(context: WorkflowContext) -> None:
    memory_id = _extract_memory_id(context)
    if memory_id is None:
        return
    repo = MemoryRepository(context.session)
    memory = repo.get(memory_id)
    if memory is None:
        logger.debug("Memory %s not found for indexing", memory_id)
        return
    rag = RAGService(context.session)
    rag.index_memory(memory)


def _delete_embedding_step(context: WorkflowContext) -> None:
    memory_id = _extract_memory_id(context)
    if memory_id is None:
        return
    rag = RAGService(context.session)
    rag.delete_memory_embedding(memory_id)


def register_default_workflows(engine: WorkflowEngine) -> None:
    """Register built-in workflows for the domain."""

    engine.register(
        Workflow(
            name="memory-index-on-create",
            event="memory.created",
            steps=[_index_memory_step],
        )
    )

    engine.register(
        Workflow(
            name="memory-reindex-on-update",
            event="memory.updated",
            steps=[_index_memory_step],
        )
    )

    engine.register(
        Workflow(
            name="memory-embedding-delete",
            event="memory.deleted",
            steps=[_delete_embedding_step],
        )
    )

