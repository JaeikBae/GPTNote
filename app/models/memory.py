"""Memory ORM model representing captured knowledge objects."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Memory(Base):
    """Stores captured thoughts, notes, and contextual data."""

    __tablename__ = "memories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_device: Mapped[str | None] = mapped_column(String(100))
    source_location: Mapped[str | None] = mapped_column(String(255))
    context: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    owner: Mapped["User"] = relationship(back_populates="memories")
    attachments: Mapped[list["Attachment"]] = relationship(
        back_populates="memory", cascade="all, delete-orphan"
    )


from app.models.attachment import Attachment  # noqa: E402
from app.models.user import User  # noqa: E402

