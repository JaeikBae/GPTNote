"""Business logic for file attachments."""

import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Attachment
from app.repositories import AttachmentRepository


class AttachmentService:
    """Handles storage and retrieval of attachments."""

    def __init__(self, session: Session):
        self.repo = AttachmentRepository(session)
        self.settings = get_settings()

    def _memory_storage_dir(self, memory_id: uuid.UUID) -> Path:
        path = self.settings.storage_dir / "attachments" / str(memory_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_attachment(
        self, memory_id: uuid.UUID, upload: UploadFile
    ) -> Attachment:
        storage_dir = self._memory_storage_dir(memory_id)
        safe_name = Path(upload.filename).name
        file_path = storage_dir / safe_name
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)

        attachment = Attachment(
            memory_id=memory_id,
            filename=safe_name,
            content_type=upload.content_type,
            size_bytes=file_path.stat().st_size,
            storage_path=str(file_path.resolve()),
        )
        return self.repo.create(attachment)

    def get_attachment(self, attachment_id: uuid.UUID) -> Attachment | None:
        return self.repo.get(attachment_id)

    def list_for_memory(self, memory_id: uuid.UUID) -> list[Attachment]:
        return self.repo.list_for_memory(memory_id)

    def delete_attachment(self, attachment: Attachment) -> None:
        file_path = Path(attachment.storage_path)
        if file_path.exists():
            file_path.unlink()
        self.repo.delete(attachment)

