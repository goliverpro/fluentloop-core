from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.middleware.auth import get_current_user
from app.db.supabase import get_supabase
from app.models import CreateSessionRequest
from app.services import sessions as sessions_service
from app.services import users as users_service

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_session(body: CreateSessionRequest, current_user=Depends(get_current_user)):
    supabase = get_supabase()
    session = sessions_service.create_session(
        supabase,
        current_user.id,
        body.type,
        body.pillar,
        body.scenario_id,
    )
    return session


@router.get("/")
async def list_sessions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user=Depends(get_current_user),
):
    supabase = get_supabase()
    sessions = sessions_service.list_sessions(supabase, current_user.id, limit, offset)
    return sessions


@router.get("/{session_id}")
async def get_session(session_id: str, current_user=Depends(get_current_user)):
    supabase = get_supabase()
    session = sessions_service.get_session(supabase, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    messages = sessions_service.get_session_messages(supabase, session_id)
    return {**session, "messages": messages}


@router.patch("/{session_id}/end")
async def end_session(session_id: str, current_user=Depends(get_current_user)):
    supabase = get_supabase()
    session = sessions_service.get_session(supabase, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.get("ended_at"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session already ended")

    result = sessions_service.end_session(supabase, session_id, current_user.id)

    profile = users_service.get_user_profile(supabase, current_user.id)
    new_level = sessions_service.check_level_up(supabase, current_user.id, profile["level"])
    level_up = None
    if new_level:
        users_service.update_user_level(supabase, current_user.id, new_level)
        supabase.table("user_levels").insert({
            "user_id": current_user.id,
            "level": new_level,
            "source": "auto",
        }).execute()
        level_up = new_level

    return {**result, "level_up": level_up}
