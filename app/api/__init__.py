"""API package for FastAPI routers."""

from fastapi import APIRouter

from app.api.v1 import attachments, memories, users

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(memories.router, prefix="/memories", tags=["memories"])
api_router.include_router(
    attachments.router, prefix="/memories", tags=["attachments"]
)

__all__ = ["api_router"]
