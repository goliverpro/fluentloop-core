import json
import re
from typing import AsyncGenerator

import anthropic
from supabase import Client

from app.config import settings
from app.services.users import (
    check_and_reset_daily_limit,
    check_daily_limit,
    increment_daily_usage,
    get_user_profile,
)
from app.services.sessions import get_session, get_session_messages
from app.services.scenarios import get_scenario


SYSTEM_PROMPT_BASE = """You are an English conversation tutor helping a Brazilian learner practice English.

User level: {level}

Guidelines:
- Always respond in English
- Keep responses natural, conversational, and appropriate for {level} level
- Gently encourage the learner
- After your response, if the user made grammar or vocabulary errors, include a corrections block in this exact JSON format at the very end:

<corrections>
{{"corrections": [{{"original": "text with error", "corrected": "corrected text", "type": "grammar|vocabulary", "explanation": "brief explanation in Portuguese"}}]}}
</corrections>

If there are no errors, omit the corrections block entirely."""

SYSTEM_PROMPT_SCENARIO = """You are playing the role of {ai_role} in a roleplay scenario: "{scenario_name}".

{scenario_description}

User level: {level}

Guidelines:
- Stay in character throughout the conversation
- Use natural English appropriate for the scenario and {level} level
- After your response, if the user made grammar or vocabulary errors, include a corrections block in this exact JSON format at the very end:

<corrections>
{{"corrections": [{{"original": "text with error", "corrected": "corrected text", "type": "grammar|vocabulary", "explanation": "brief explanation in Portuguese"}}]}}
</corrections>

If there are no errors, omit the corrections block entirely."""


def _build_system_prompt(user_level: str, scenario: dict | None) -> str:
    if scenario:
        return SYSTEM_PROMPT_SCENARIO.format(
            ai_role=scenario["ai_role"],
            scenario_name=scenario["name"],
            scenario_description=scenario.get("description", ""),
            level=user_level,
        )
    return SYSTEM_PROMPT_BASE.format(level=user_level)


def _extract_corrections(text: str) -> tuple[str, list[dict]]:
    corrections = []
    match = re.search(r"<corrections>(.*?)</corrections>", text, re.DOTALL)
    if match:
        raw = match.group(1).strip()
        try:
            data = json.loads(raw)
            corrections = data.get("corrections", [])
        except json.JSONDecodeError:
            pass
        clean_text = text[: match.start()].rstrip()
    else:
        clean_text = text
    return clean_text, corrections


def _persist_message(supabase: Client, session_id: str, role: str, content: str) -> dict:
    response = (
        supabase.table("messages")
        .insert({"session_id": session_id, "role": role, "content": content})
        .select("id, role, content, audio_url, created_at")
        .single()
        .execute()
    )
    return response.data


def _persist_corrections(supabase: Client, message_id: str, corrections: list[dict]) -> None:
    if not corrections:
        return
    records = [
        {
            "message_id": message_id,
            "original_text": c.get("original", ""),
            "corrected_text": c.get("corrected", ""),
            "error_type": c.get("type", "grammar"),
            "explanation": c.get("explanation", ""),
        }
        for c in corrections
    ]
    supabase.table("corrections").insert(records).execute()


async def stream_chat(
    supabase: Client,
    user,
    session_id: str,
    content: str,
    is_voice: bool,
) -> AsyncGenerator[str, None]:
    user_id = user.id

    profile = get_user_profile(supabase, user_id)
    profile = check_and_reset_daily_limit(supabase, profile)

    if not check_daily_limit(profile):
        yield "data: [LIMIT_REACHED]\n\n"
        return

    session = get_session(supabase, session_id, user_id)
    if not session:
        yield "data: [SESSION_NOT_FOUND]\n\n"
        return

    scenario = None
    if session.get("scenario_id"):
        scenario = get_scenario(supabase, session["scenario_id"])

    history = get_session_messages(supabase, session_id)
    messages = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in history[-20:]
    ]
    messages.append({"role": "user", "content": content})

    system_prompt = _build_system_prompt(profile["level"], scenario)

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        full_response = ""

        with client.messages.stream(
            model="claude-3-5-haiku-20241022",
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
        ) as stream:
            for text_chunk in stream.text_stream:
                full_response += text_chunk
                yield f"data: {json.dumps(text_chunk)}\n\n"

        clean_text, corrections = _extract_corrections(full_response)

        _persist_message(supabase, session_id, "user", content)
        ai_msg = _persist_message(supabase, session_id, "assistant", clean_text)

        if corrections:
            _persist_corrections(supabase, ai_msg["id"], corrections)

        increment_daily_usage(supabase, user_id, profile["daily_interactions_used"])

        if corrections:
            yield f"data: [CORRECTIONS]{json.dumps(corrections)}\n\n"

        yield "data: [DONE]\n\n"

    except anthropic.AuthenticationError:
        yield "data: [ERROR]Service temporarily unavailable\n\n"
    except Exception as e:
        yield f"data: [ERROR]{str(e)}\n\n"
