from supabase import Client


def create_session(supabase: Client, user_id: str, session_type: str, pillar: str, scenario_id: str | None) -> dict:
    payload = {
        "user_id": user_id,
        "type": session_type,
        "pillar": pillar,
        "scenario_id": scenario_id,
    }
    response = (
        supabase.table("sessions")
        .insert(payload)
        .select("id, type, pillar, scenario_id, started_at, ended_at, total_messages, error_rate")
        .single()
        .execute()
    )
    return response.data


def get_session(supabase: Client, session_id: str, user_id: str) -> dict | None:
    response = (
        supabase.table("sessions")
        .select("id, type, pillar, scenario_id, started_at, ended_at, total_messages, error_rate")
        .eq("id", session_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    return response.data


def list_sessions(supabase: Client, user_id: str, limit: int = 20, offset: int = 0) -> list[dict]:
    response = (
        supabase.table("sessions")
        .select(
            "id, type, pillar, scenario_id, scenarios(name), started_at, ended_at, total_messages, error_rate"
        )
        .eq("user_id", user_id)
        .order("started_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return response.data


def get_session_messages(supabase: Client, session_id: str) -> list[dict]:
    response = (
        supabase.table("messages")
        .select("id, role, content, audio_url, created_at, corrections(id, original_text, corrected_text, error_type, explanation)")
        .eq("session_id", session_id)
        .order("created_at", desc=False)
        .execute()
    )
    return response.data


def end_session(supabase: Client, session_id: str, user_id: str) -> dict:
    from datetime import datetime, timezone

    # Busca mensagens do usuário para calcular error_rate
    messages = (
        supabase.table("messages")
        .select("id")
        .eq("session_id", session_id)
        .eq("role", "user")
        .execute()
    )
    user_message_ids = [m["id"] for m in messages.data]
    total = len(user_message_ids)

    error_rate = None
    if total > 0:
        corrections = (
            supabase.table("corrections")
            .select("message_id")
            .in_("message_id", user_message_ids)
            .execute()
        )
        messages_with_errors = len({c["message_id"] for c in corrections.data})
        error_rate = round((messages_with_errors / total) * 100, 2)

    now = datetime.now(timezone.utc).isoformat()
    response = (
        supabase.table("sessions")
        .update({
            "ended_at": now,
            "total_messages": total,
            "error_rate": error_rate,
        })
        .eq("id", session_id)
        .eq("user_id", user_id)
        .select("id, ended_at, total_messages, error_rate")
        .single()
        .execute()
    )
    return response.data


def check_level_up(supabase: Client, user_id: str, current_level: str) -> str | None:
    """
    Verifica se o usuário atingiu o critério de avanço de nível:
    5 sessões consecutivas com error_rate < 20%.
    Retorna o novo nível se deve avançar, None caso contrário.
    """
    LEVEL_UP_MAP = {"A2": "B1", "B1": "B2"}
    if current_level not in LEVEL_UP_MAP:
        return None

    recent = (
        supabase.table("sessions")
        .select("error_rate")
        .eq("user_id", user_id)
        .not_.is_("ended_at", "null")
        .not_.is_("error_rate", "null")
        .order("started_at", desc=True)
        .limit(5)
        .execute()
    )

    sessions = recent.data
    if len(sessions) < 5:
        return None

    if all(s["error_rate"] < 20 for s in sessions):
        return LEVEL_UP_MAP[current_level]

    return None
