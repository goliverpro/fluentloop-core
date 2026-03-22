from fastapi import APIRouter, Depends
from app.middleware.auth import get_current_user

router = APIRouter()


@router.post("/")
async def create_session(current_user=Depends(get_current_user)):
    # TODO: create session record in Supabase
    raise NotImplementedError


@router.get("/")
async def list_sessions(current_user=Depends(get_current_user)):
    # TODO: list sessions with pagination
    raise NotImplementedError


@router.get("/{session_id}")
async def get_session(session_id: str, current_user=Depends(get_current_user)):
    # TODO: get session detail with messages and corrections
    raise NotImplementedError


@router.patch("/{session_id}/end")
async def end_session(session_id: str, current_user=Depends(get_current_user)):
    # TODO: calculate error_rate, check level-up criteria, persist
    raise NotImplementedError
