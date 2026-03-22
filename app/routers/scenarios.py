from fastapi import APIRouter, Depends
from app.middleware.auth import get_current_user

router = APIRouter()


@router.get("/")
async def list_scenarios(current_user=Depends(get_current_user)):
    # TODO: list scenarios filtered by user plan
    raise NotImplementedError
