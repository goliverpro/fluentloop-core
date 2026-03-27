import json
import re
from typing import AsyncGenerator

from openai import OpenAI, AuthenticationError
from supabase import Client

from app.config import settings
from app.services.users import (
    check_and_reset_daily_limit,
    check_daily_limit,
    increment_daily_usage,
    get_user_profile,
)
from app.services.sessions import get_session, get_session_messages, update_session_stats
from app.services.scenarios import get_scenario


CORRECTIONS_BLOCK = """
---
GRAMMAR CORRECTION RULES (mandatory):
After EVERY user message, review it strictly for ALL of the following errors:
- Wrong subject pronoun (e.g. "Can you ask you" → "Can I ask you")
- Missing or wrong auxiliary verb (do/does/did/will/would/can/could/should)
- Wrong verb tense (e.g. "I go yesterday" → "I went yesterday")
- Subject-verb agreement (e.g. "He go" → "He goes")
- Wrong preposition, article (a/an/the), or word order
- Wrong or missing plural/singular
- Vocabulary misuse (wrong word choice)

If you find ANY error, include this block at the very end of your response:
<corrections>
{{"corrections": [{{"original": "exact phrase with error", "corrected": "corrected phrase", "type": "grammar|vocabulary", "explanation": "explicação curta em português"}}]}}
</corrections>

Only omit the block if the message is genuinely error-free. When in doubt, include the correction."""

SYSTEM_PROMPT_BASE = """You are an English conversation tutor helping a Brazilian learner practice English.

User level: {level}

Guidelines:
- Always respond in English
- Keep responses natural, conversational, and appropriate for {level} level
- Gently encourage the learner
""" + CORRECTIONS_BLOCK

SYSTEM_PROMPT_SCENARIO = (
    """You are playing the role of {ai_role} in a roleplay scenario: "{scenario_name}".

{scenario_description}

User level: {level}

Guidelines:
- Stay in character throughout the conversation
- Use natural English appropriate for the scenario and {level} level
"""
    + CORRECTIONS_BLOCK
)


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
    response = supabase.table("messages").insert({"session_id": session_id, "role": role, "content": content}).execute()
    return response.data[0]


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
        client = OpenAI(api_key=settings.openai_api_key)
        full_response = ""

        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1024,
            messages=[{"role": "system", "content": system_prompt}] + messages,
            stream=True,
        )
        for chunk in stream:
            text_chunk = chunk.choices[0].delta.content or ""
            if text_chunk:
                full_response += text_chunk
                yield f"data: {json.dumps(text_chunk)}\n\n"

        clean_text, corrections = _extract_corrections(full_response)

        user_msg = _persist_message(supabase, session_id, "user", content)
        _persist_message(supabase, session_id, "assistant", clean_text)

        if corrections:
            # Correções vinculadas à mensagem do USUÁRIO (a que contém o erro)
            _persist_corrections(supabase, user_msg["id"], corrections)

        # Atualiza stats da sessão ao vivo após cada troca
        update_session_stats(supabase, session_id)

        increment_daily_usage(supabase, user_id, profile["daily_interactions_used"])

        if corrections:
            yield f"data: [CORRECTIONS]{json.dumps(corrections)}\n\n"

        yield "data: [DONE]\n\n"

    except AuthenticationError:
        yield "data: [ERROR]Service temporarily unavailable\n\n"
    except Exception as e:
        yield f"data: [ERROR]{str(e)}\n\n"
