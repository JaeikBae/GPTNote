"""Business logic for user management."""

import uuid

from sqlalchemy.orm import Session

from app.models import User
from app.repositories import UserRepository
from app.schemas import UserCreate
from app.utils import hash_password


class UserService:
    """Provide user-related operations."""

    def __init__(self, session: Session):
        self.repo = UserRepository(session)

    def create_user(self, payload: UserCreate) -> User:
        if self.repo.get_by_email(payload.email):
            raise ValueError("Email already registered")
        user = User(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
        )
        return self.repo.create(user)

    def get_user(self, user_id: uuid.UUID) -> User | None:
        return self.repo.get_by_id(user_id)

    def list_users(self) -> list[User]:
        return self.repo.list()

