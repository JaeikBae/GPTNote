"""Memory API endpoints."""

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas import MemoryCreate, MemoryRead, MemoryReadWithAttachments, MemoryUpdate
from app.services import (
    AttachmentService,
    MemoryService,
    TranscriptionError,
    TranscriptionNotConfigured,
    TranscriptionService,
)


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


@router.post(
    "/transcribe",
    response_model=MemoryReadWithAttachments,
    status_code=status.HTTP_201_CREATED,
)
async def create_memory_from_audio(
    owner_id: uuid.UUID = Form(..., description="Owner identifier"),
    file: UploadFile = File(..., description="Audio file to transcribe"),
    title: str | None = Form(None, description="Optional title for the memory"),
    tags: str | None = Form(None, description="Tags as JSON array or comma-separated string"),
    captured_at: str | None = Form(None, description="ISO8601 datetime when audio was captured"),
    source_device: str | None = Form(None),
    source_location: str | None = Form(None),
    context: str | None = Form(None, description="Arbitrary JSON metadata"),
    db: Session = Depends(deps.get_db),
) -> MemoryReadWithAttachments:
    """Transcribe an uploaded audio file and store it as a memory with attachment."""

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Uploaded audio file is empty")

    transcriber = TranscriptionService()
    try:
        transcription = transcriber.transcribe_audio(
            audio_bytes,
            filename=file.filename,
            content_type=file.content_type,
        )
    except TranscriptionNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except TranscriptionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    transcript_text = transcription.text.strip()
    if not transcript_text:
        raise HTTPException(status_code=422, detail="Transcription produced empty content")

    tags_list = _parse_tags(tags)
    captured_at_dt = _parse_captured_at(captured_at)
    recorded_at = captured_at_dt or datetime.now(timezone.utc)
    context_payload = _parse_context(context)
    context_payload = context_payload or {}
    context_payload.setdefault(
        "transcription",
        {
            "source": "audio_transcription",
            "filename": file.filename,
            "content_type": file.content_type,
            "transcribed_at": datetime.now(timezone.utc).isoformat(),
            "transcription_model": transcriber.settings.openai_transcription_model,
        },
    )

    memory_payload = MemoryCreate(
        owner_id=owner_id,
        title=_derive_title(transcript_text, title),
        content=transcript_text,
        tags=tags_list,
        captured_at=recorded_at,
        source_device=source_device,
        source_location=source_location,
        context=context_payload,
    )

    memory_service = MemoryService(db)
    memory = memory_service.create_memory(memory_payload)

    # Reset file pointer so we can persist the original audio as an attachment.
    file.file.seek(0)
    attachment_service = AttachmentService(db)
    attachment_service.save_attachment(memory.id, file)

    refreshed = memory_service.get_memory(memory.id)
    return MemoryReadWithAttachments.model_validate(refreshed)


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


def _parse_tags(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = None

    if isinstance(parsed, list):
        return [str(item).strip() for item in parsed if str(item).strip()]

    # Fallback to comma-separated parsing
    return [tag.strip() for tag in raw.split(",") if tag.strip()]


def _parse_context(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:  # noqa: B904
        raise HTTPException(status_code=400, detail="context must be valid JSON") from exc
    if not isinstance(parsed, dict):
        raise HTTPException(status_code=400, detail="context must be a JSON object")
    return parsed


def _parse_captured_at(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:  # noqa: B904
        raise HTTPException(
            status_code=400,
            detail="captured_at must be an ISO8601 datetime string",
        ) from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _derive_title(transcript: str, provided: str | None) -> str:
    if provided and provided.strip():
        return provided.strip()
    collapsed = " ".join(transcript.split())
    if not collapsed:
        return "음성 메모"
    max_length = 48
    if len(collapsed) <= max_length:
        return collapsed
    return f"{collapsed[:max_length]}…"

