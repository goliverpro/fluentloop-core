from typing import Optional
from pydantic import BaseModel


class CreateSessionRequest(BaseModel):
    type: str
    pillar: str
    scenario_id: Optional[str] = None


class MessageRequest(BaseModel):
    session_id: str
    content: str
    is_voice: bool = False


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None


class UpdateLevelRequest(BaseModel):
    level: str


class TtsRequest(BaseModel):
    text: str
    voice: str = "alloy"


class CheckoutRequest(BaseModel):
    plan_type: str  # "monthly" | "annual"


class CorrectionResponse(BaseModel):
    id: str
    original_text: str
    corrected_text: str
    error_type: str
    explanation: str


class PronunciationWordResponse(BaseModel):
    word: str
    position: int
    accuracy_score: float
    phoneme_feedback: Optional[str] = None


class UserProfileResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    avatar_url: Optional[str]
    level: str
    plan: str
    daily_interactions_used: int
    daily_reset_at: str


class ScenarioResponse(BaseModel):
    id: str
    name: str
    description: str
    ai_role: str
    category: str
    difficulty: str
    is_free: bool


class SessionResponse(BaseModel):
    id: str
    type: str
    pillar: str
    scenario_id: Optional[str]
    started_at: str
    ended_at: Optional[str]
    total_messages: Optional[int]
    error_rate: Optional[float]


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    audio_url: Optional[str]
    created_at: str
    corrections: list[CorrectionResponse]


class SubscriptionResponse(BaseModel):
    id: str
    user_id: str
    stripe_subscription_id: str
    plan_type: str
    status: str
    current_period_start: str
    current_period_end: str
