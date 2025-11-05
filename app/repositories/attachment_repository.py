"""Repository for attachment persistence."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Attachment


class AttachmentRepository:
    """Encapsulates storage for attachments."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, attachment: Attachment) -> Attachment:
        self.session.add(attachment)
        self.session.commit()
        self.session.refresh(attachment)
        return attachment

    def get(self, attachment_id: uuid.UUID) -> Attachment | None:
        return self.session.get(Attachment, attachment_id)

    def list_for_memory(self, memory_id: uuid.UUID) -> list[Attachment]:
        stmt = (
            select(Attachment)
            .where(Attachment.memory_id == memory_id)
            .order_by(Attachment.created_at.desc())
        )
        return list(self.session.scalars(stmt).all())

    def delete(self, attachment: Attachment) -> None:
        self.session.delete(attachment)
        self.session.commit()

