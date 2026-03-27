from fastapi import APIRouter, Depends, HTTPException, status

from app.middleware.auth import get_current_user
from app.db.supabase import get_supabase
from app.models import UpdateProfileRequest, UpdateLevelRequest, UserProfileResponse
from app.services import users as users_service

router = APIRouter()

VALID_LEVELS = {"A2", "B1", "B2"}


@router.get("/me", response_model=UserProfileResponse)
async def get_me(current_user=Depends(get_current_user)):
    supabase = get_supabase()
    profile = users_service.get_user_profile(supabase, current_user.id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return profile


@router.patch("/me", response_model=UserProfileResponse)
async def update_me(body: UpdateProfileRequest, current_user=Depends(get_current_user)):
    supabase = get_supabase()
    payload = body.model_dump(exclude_none=True)
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")
    profile = users_service.update_user_profile(supabase, current_user.id, payload)
    return profile


@router.patch("/me/level", response_model=UserProfileResponse)
async def update_level(body: UpdateLevelRequest, current_user=Depends(get_current_user)):
    if body.level not in VALID_LEVELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid level. Must be one of: {', '.join(VALID_LEVELS)}",
        )
    supabase = get_supabase()
    updated = users_service.update_user_level(supabase, current_user.id, body.level)
    supabase.table("user_levels").insert({
        "user_id": current_user.id,
        "level": body.level,
        "source": "manual",
    }).execute()
    profile = users_service.get_user_profile(supabase, current_user.id)
    return profile
