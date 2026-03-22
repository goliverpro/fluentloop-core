from supabase import Client


def list_scenarios(supabase: Client, user_plan: str) -> list[dict]:
    query = supabase.table("scenarios").select(
        "id, name, description, ai_role, category, difficulty, is_free"
    )
    if user_plan != "pro":
        query = query.eq("is_free", True)
    response = query.order("name").execute()
    return response.data


def get_scenario(supabase: Client, scenario_id: str) -> dict | None:
    response = (
        supabase.table("scenarios")
        .select("id, name, description, ai_role, category, difficulty, is_free")
        .eq("id", scenario_id)
        .single()
        .execute()
    )
    return response.data
