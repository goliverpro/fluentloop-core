from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_env: str = "development"
    app_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"

    # Supabase
    supabase_url: str
    supabase_service_role_key: str

    # Anthropic (não usado no MVP — chat usa OpenAI)
    anthropic_api_key: str = ""

    # Azure Speech (não usado no MVP — STT usa OpenAI Whisper)
    azure_speech_key: str = ""
    azure_speech_region: str = "brazilsouth"

    # OpenAI
    openai_api_key: str

    # Stripe
    stripe_secret_key: str
    stripe_webhook_secret: str
    stripe_monthly_price_id: str
    stripe_annual_price_id: str

    @property
    def allowed_origins(self) -> list[str]:
        origins = [self.frontend_url]
        if self.app_env == "development":
            origins.append("http://localhost:3000")
        return origins

    class Config:
        env_file = ".env"


settings = Settings()
