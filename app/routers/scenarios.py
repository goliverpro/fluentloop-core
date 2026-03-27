from fastapi import APIRouter, Depends

from app.middleware.auth import get_current_user
from app.db.supabase import get_supabase
from app.services import users as users_service
from app.services.scenarios import list_scenarios

router = APIRouter()


@router.get("/")
async def get_scenarios(current_user=Depends(get_current_user)):
    supabase = get_supabase()
    profile = users_service.get_user_profile(supabase, current_user.id)
    scenarios = list_scenarios(supabase, profile["plan"])
    return scenarios
