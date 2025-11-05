"""Attachment upload and download API."""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas import AttachmentRead
from app.services import AttachmentService, MemoryService


router = APIRouter()


@router.post("/{memory_id}/attachments", response_model=AttachmentRead)
async def upload_attachment(
    memory_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
) -> AttachmentRead:
    """Upload a file attachment for a memory."""

    memory_service = MemoryService(db)
    memory = memory_service.get_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    attachment_service = AttachmentService(db)
    attachment = attachment_service.save_attachment(memory_id, file)
    return AttachmentRead.model_validate(attachment)


@router.get("/{memory_id}/attachments", response_model=list[AttachmentRead])
def list_attachments(
    memory_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
) -> list[AttachmentRead]:
    """List attachments for a memory."""

    memory_service = MemoryService(db)
    memory = memory_service.get_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    attachment_service = AttachmentService(db)
    attachments = attachment_service.list_for_memory(memory_id)
    return [AttachmentRead.model_validate(item) for item in attachments]


@router.get("/{memory_id}/attachments/{attachment_id}")
def download_attachment(
    memory_id: uuid.UUID,
    attachment_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
) -> FileResponse:
    """Download a previously uploaded attachment."""

    attachment_service = AttachmentService(db)
    attachment = attachment_service.get_attachment(attachment_id)
    if not attachment or attachment.memory_id != memory_id:
        raise HTTPException(status_code=404, detail="Attachment not found")

    file_path = Path(attachment.storage_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Stored file missing")

    return FileResponse(
        path=file_path,
        filename=attachment.filename,
        media_type=attachment.content_type or "application/octet-stream",
    )


@router.delete("/{memory_id}/attachments/{attachment_id}")
def delete_attachment(
    memory_id: uuid.UUID,
    attachment_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
) -> None:
    """Delete an attachment and remove its file."""

    attachment_service = AttachmentService(db)
    attachment = attachment_service.get_attachment(attachment_id)
    if not attachment or attachment.memory_id != memory_id:
        raise HTTPException(status_code=404, detail="Attachment not found")
    attachment_service.delete_attachment(attachment)

