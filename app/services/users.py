from uuid import UUID
from supabase import Client


def get_user_profile(supabase: Client, user_id: str) -> dict:
    response = (
        supabase.table("users")
        .select("id, email, name, avatar_url, level, plan, daily_interactions_used, daily_reset_at")
        .eq("id", user_id)
        .single()
        .execute()
    )
    return response.data


def update_user_profile(supabase: Client, user_id: str, payload: dict) -> dict:
    response = (
        supabase.table("users")
        .update(payload)
        .eq("id", user_id)
        .select("id, email, name, avatar_url, level, plan, daily_interactions_used, daily_reset_at")
        .single()
        .execute()
    )
    return response.data


def update_user_level(supabase: Client, user_id: str, new_level: str) -> dict:
    response = (
        supabase.table("users")
        .update({"level": new_level})
        .eq("id", user_id)
        .select("id, level")
        .single()
        .execute()
    )
    return response.data


def check_and_reset_daily_limit(supabase: Client, user: dict) -> dict:
    """
    Verifica se o contador diário precisa ser zerado (novo dia).
    Retorna o perfil atualizado.
    """
    from datetime import datetime, timezone, timedelta

    reset_at = datetime.fromisoformat(user["daily_reset_at"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    next_reset = reset_at + timedelta(days=1)

    if now >= next_reset:
        updated = (
            supabase.table("users")
            .update({"daily_interactions_used": 0, "daily_reset_at": now.isoformat()})
            .eq("id", user["id"])
            .select("id, plan, daily_interactions_used, daily_reset_at")
            .single()
            .execute()
        )
        return updated.data

    return user


def check_daily_limit(user: dict) -> bool:
    """Retorna True se o usuário ainda tem interações disponíveis."""
    FREE_DAILY_LIMIT = 10
    if user["plan"] == "pro":
        return True
    return user["daily_interactions_used"] < FREE_DAILY_LIMIT


def increment_daily_usage(supabase: Client, user_id: str, current_count: int) -> None:
    supabase.table("users").update(
        {"daily_interactions_used": current_count + 1}
    ).eq("id", user_id).execute()
