from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.middleware.auth import get_current_user
from app.db.supabase import get_supabase
from app.models import MessageRequest
from app.services.chat import stream_chat

router = APIRouter()


@router.post("/message")
async def send_message(body: MessageRequest, current_user=Depends(get_current_user)):
    supabase = get_supabase()
    return StreamingResponse(
        stream_chat(supabase, current_user, body.session_id, body.content, body.is_voice),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
