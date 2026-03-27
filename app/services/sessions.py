from supabase import Client


def create_session(supabase: Client, user_id: str, session_type: str, pillar: str, scenario_id: str | None) -> dict:
    payload = {
        "user_id": user_id,
        "type": session_type,
        "pillar": pillar,
        "scenario_id": scenario_id,
    }
    response = supabase.table("sessions").insert(payload).execute()
    return response.data[0]


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

    sessions = response.data

    # Normaliza scenarios(name) → scenario_name
    for s in sessions:
        scenarios = s.pop("scenarios", None)
        s["scenario_name"] = (scenarios or {}).get("name")

    # Para sessões ativas (total_messages ainda null), conta mensagens ao vivo
    active_ids = [s["id"] for s in sessions if s.get("total_messages") is None]
    if active_ids:
        counts_resp = (
            supabase.table("messages")
            .select("session_id")
            .in_("session_id", active_ids)
            .eq("role", "user")
            .execute()
        )
        count_map: dict[str, int] = {}
        for m in counts_resp.data:
            sid = m["session_id"]
            count_map[sid] = count_map.get(sid, 0) + 1

        for s in sessions:
            if s.get("total_messages") is None:
                s["total_messages"] = count_map.get(s["id"], 0)

    return sessions


def get_session_messages(supabase: Client, session_id: str) -> list[dict]:
    response = (
        supabase.table("messages")
        .select("id, role, content, audio_url, created_at, corrections(id, original_text, corrected_text, error_type, explanation)")
        .eq("session_id", session_id)
        .order("created_at", desc=False)
        .execute()
    )
    return response.data


def update_session_stats(supabase: Client, session_id: str) -> None:
    """Recalcula e grava total_messages e error_rate após cada mensagem."""
    user_msgs = (
        supabase.table("messages")
        .select("id")
        .eq("session_id", session_id)
        .eq("role", "user")
        .execute()
    )
    user_message_ids = [m["id"] for m in user_msgs.data]
    total = len(user_message_ids)

    if total == 0:
        return

    corrections = (
        supabase.table("corrections")
        .select("message_id")
        .in_("message_id", user_message_ids)
        .execute()
    )
    messages_with_errors = len({c["message_id"] for c in corrections.data})
    error_rate = round((messages_with_errors / total) * 100, 2)

    supabase.table("sessions").update({
        "total_messages": total,
        "error_rate": error_rate,
    }).eq("id", session_id).execute()


def end_session(supabase: Client, session_id: str, user_id: str) -> dict:
    from datetime import datetime, timezone

    update_session_stats(supabase, session_id)

    now = datetime.now(timezone.utc).isoformat()
    response = (
        supabase.table("sessions")
        .update({"ended_at": now})
        .eq("id", session_id)
        .eq("user_id", user_id)
        .execute()
    )
    return response.data[0]


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
