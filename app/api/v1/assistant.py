"""Assistant chat API."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas import AssistantChatRequest, AssistantChatResponse
from app.services import AssistantService


router = APIRouter()


@router.post("/chat", response_model=AssistantChatResponse)
def chat_with_assistant(
    payload: AssistantChatRequest,
    db: Session = Depends(deps.get_db),
) -> AssistantChatResponse:
    """Send a message to the MindDock assistant."""

    service = AssistantService(db)
    response = service.chat(payload)
    return response
