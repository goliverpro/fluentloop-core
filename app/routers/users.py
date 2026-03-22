from fastapi import APIRouter, Depends
from app.middleware.auth import get_current_user

router = APIRouter()


@router.get("/me")
async def get_me(current_user=Depends(get_current_user)):
    # TODO: fetch user profile from Supabase
    raise NotImplementedError


@router.patch("/me")
async def update_me(current_user=Depends(get_current_user)):
    # TODO: update name / avatar
    raise NotImplementedError


@router.patch("/me/level")
async def update_level(current_user=Depends(get_current_user)):
    # TODO: update level + insert user_levels record
    raise NotImplementedError
