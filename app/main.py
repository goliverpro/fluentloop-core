from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.routers import users, sessions, chat, speech, scenarios, billing

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="FluentLoop API",
    description="AI-powered English conversation practice",
    version="1.0.0",
    docs_url="/docs" if settings.app_env == "development" else None,
    redoc_url=None,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Routers
app.include_router(users.router, prefix="/v1/users", tags=["users"])
app.include_router(sessions.router, prefix="/v1/sessions", tags=["sessions"])
app.include_router(chat.router, prefix="/v1/chat", tags=["chat"])
app.include_router(speech.router, prefix="/v1/speech", tags=["speech"])
app.include_router(scenarios.router, prefix="/v1/scenarios", tags=["scenarios"])
app.include_router(billing.router, prefix="/v1/billing", tags=["billing"])


@app.get("/health")
async def health():
    return {"status": "ok"}
