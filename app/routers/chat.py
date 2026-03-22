from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.middleware.auth import get_current_user

router = APIRouter()


class MessageRequest(BaseModel):
    session_id: str
    content: str = Field(..., min_length=1, max_length=1000)
    is_voice: bool = False


@router.post("/message")
async def send_message(
    request: Request,
    body: MessageRequest,
    current_user=Depends(get_current_user),
):
    # TODO: implement streaming chat with Claude
    # 1. Check daily limit
    # 2. Fetch session history
    # 3. Build prompt
    # 4. Stream Claude response
    # 5. Extract corrections
    # 6. Persist to Supabase
    raise NotImplementedError
