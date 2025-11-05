"""User schema definitions."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserRead(UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }

