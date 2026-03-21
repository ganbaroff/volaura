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
        return [self.app_url]


settings = Settings()
