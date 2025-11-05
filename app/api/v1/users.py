"""User API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas import UserCreate, UserRead
from app.services import UserService


router = APIRouter()


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(deps.get_db)) -> UserRead:
    """Register a new user."""

    service = UserService(db)
    try:
        user = service.create_user(payload)
    except ValueError as exc:  # email already registered
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return UserRead.model_validate(user)


@router.get("/{user_id}", response_model=UserRead)
def read_user(user_id: uuid.UUID, db: Session = Depends(deps.get_db)) -> UserRead:
    """Fetch a single user by identifier."""

    service = UserService(db)
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead.model_validate(user)


@router.get("/", response_model=list[UserRead])
def list_users(db: Session = Depends(deps.get_db)) -> list[UserRead]:
    """List users sorted by most recent."""

    service = UserService(db)
    users = service.list_users()
    return [UserRead.model_validate(user) for user in users]

