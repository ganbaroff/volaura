from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Supabase
    supabase_url: str = "http://127.0.0.1:54321"
    supabase_service_key: str = ""
    supabase_anon_key: str = ""

    # API
    api_port: int = 8000
    app_env: str = "development"
    app_url: str = "http://localhost:3000"

    # LLM
    gemini_api_key: str = ""
    openai_api_key: str = ""
    groq_api_key: str = ""

    # Swarm (multi-model BARS evaluation)
    swarm_enabled: bool = False

    # Telegram
    telegram_bot_token: str = ""

    # Stripe (MVP-1)
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"

    @property
    def cors_origins(self) -> list[str]:
        if self.is_dev:
            return ["http://localhost:3000", "http://127.0.0.1:3000"]
        origins = [self.app_url]
        # Always allow both custom domain and Vercel preview
        known = [
            "https://volaura.app",
            "https://www.volaura.app",
            "https://volaura-web.vercel.app",
        ]
        for k in known:
            if k not in origins:
                origins.append(k)
        return origins


settings = Settings()


def validate_production_settings() -> list[str]:
    """Check production-critical settings. Returns list of warnings."""
    warnings = []
    if not settings.is_dev:
        if not settings.gemini_api_key and not settings.openai_api_key:
            warnings.append(
                "CRITICAL: No LLM API keys configured (GEMINI_API_KEY or OPENAI_API_KEY). "
                "Open-ended assessment answers will use keyword fallback scoring."
            )
        if settings.app_url == "http://localhost:3000":
            warnings.append(
                "WARNING: APP_URL is still localhost — CORS will block frontend requests."
            )
        # Debug: log anon key status at startup
        anon_prefix = settings.supabase_anon_key[:12] if settings.supabase_anon_key else "EMPTY"
        warnings.append(f"DEBUG: SUPABASE_ANON_KEY prefix={anon_prefix}")
    return warnings
