from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Supabase
    supabase_url: str = "http://127.0.0.1:54321"
    supabase_service_key: str = ""
    # Anon key — PUBLIC key, safe to hardcode as fallback (like Stripe publishable key).
    # Supabase anon keys are designed to be exposed in browser/client-side code.
    # env var SUPABASE_ANON_KEY may be intercepted by Railway's Supabase integration;
    # ⚠️ PUBLIC anon key for Volaura Supabase project (hvykysvdkalkbswmgfut).
    # This is intentionally public — RLS enforces all access control.
    # Do NOT replace with a different project's key without understanding RLS implications.
    # SUPABASE_ANON_JWT is the unintercepted fallback name.
    # If both env vars are missing (Railway interception), the hardcoded default is used.
    _ANON_KEY_DEFAULT: str = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        ".eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh2eWt5c3Zka2Fsa2Jzd21nZnV0Iiwicm9sZSI6ImFub24i"
        "LCJpYXQiOjE3NzQyMTgyODQsImV4cCI6MjA4OTc5NDI4NH0"
        ".W4Ck1Mn8LSwMuaSg-dGnVncQeTwSwvNH2Rpp6B-JPL8"
    )
    supabase_anon_key: str = _ANON_KEY_DEFAULT
    supabase_anon_jwt: str = ""  # reads SUPABASE_ANON_JWT env var

    @property
    def effective_anon_key(self) -> str:
        """Returns the best available anon key — SUPABASE_ANON_JWT > SUPABASE_ANON_KEY > hardcoded."""
        return self.supabase_anon_jwt or self.supabase_anon_key

    @property
    def using_hardcoded_anon_key(self) -> bool:
        """True if neither env var is set and the hardcoded fallback is active."""
        return not self.supabase_anon_jwt and self.supabase_anon_key == self._ANON_KEY_DEFAULT

    # API
    api_port: int = 8000
    app_env: str = "development"
    app_url: str = "http://localhost:3000"

    # LLM — V-BRAIN chain: primary→fallback→fallback→keyword
    # GEM=aura-eyes, GRQ=quick-pulse, OAI=deep-cortex, DSK=shadow-mind
    gemini_api_key: str = ""     # GEM: primary evaluator (15 RPM free, unlimited paid)
    openai_api_key: str = ""     # OAI: tertiary fallback
    groq_api_key: str = ""       # GRQ: secondary fallback (paid tier active 2026-03-29)
    deepseek_api_key: str = ""   # DSK: experimental (swarm candidate)

    # Swarm (multi-model BARS evaluation)
    swarm_enabled: bool = False

    # Telegram — V-NERVE: CEO↔bot bidirectional + error alerting
    telegram_bot_token: str = ""
    telegram_ceo_chat_id: str = ""
    telegram_webhook_secret: str = ""

    # Monitoring — V-EYE: error tracking + performance
    sentry_dsn: str = ""         # Org: volaura, Project: volaura-api (created 2026-03-29)

    # Stripe (MVP-1)
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # BrandedBy — AI video generation
    did_api_key: str = ""  # D-ID API key (Phase 1: Lite plan $5.90/mo)
    fal_api_key: str = ""  # fal.ai API key — MuseTalk + Kling LipSync (DSP winner)

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
            "https://brandedby.xyz",
            "https://www.brandedby.xyz",
        ]
        for k in known:
            if k not in origins:
                origins.append(k)
        return origins


settings = Settings()


def assert_production_ready() -> None:
    """Raise RuntimeError for settings that will cause silent failures in production.

    Called at startup lifespan. Fails the process early rather than serving broken
    responses (e.g., CORS blocking all requests because APP_URL is still localhost).

    Only runs when APP_ENV == "production" (not staging, not development).
    """
    if settings.app_env != "production":
        return
    errors: list[str] = []
    if not settings.supabase_service_key:
        errors.append(
            "SUPABASE_SERVICE_KEY is not set — API cannot perform admin DB operations."
        )
    if settings.app_url == "http://localhost:3000":
        errors.append(
            "APP_URL is still http://localhost:3000 — CORS will block all frontend requests."
        )
    if errors:
        raise RuntimeError(
            "Production startup failed — fix these settings before deploying:\n"
            + "\n".join(f"  • {e}" for e in errors)
        )


def validate_production_settings() -> list[str]:
    """Check production-critical settings. Returns list of warnings."""
    warnings = []
    if not settings.is_dev:
        if settings.using_hardcoded_anon_key:
            warnings.append(
                "WARNING: Using hardcoded Supabase anon key fallback. "
                "Set SUPABASE_ANON_JWT on Railway to use env-based key."
            )
        if not settings.gemini_api_key and not settings.groq_api_key and not settings.openai_api_key:
            warnings.append(
                "CRITICAL: No LLM API keys configured (GEMINI_API_KEY, GROQ_API_KEY, or OPENAI_API_KEY). "
                "Open-ended assessment answers will use keyword fallback scoring."
            )
        if settings.gemini_api_key and not settings.groq_api_key:
            warnings.append(
                "WARNING: GROQ_API_KEY not set. Gemini rate-limit events (15 RPM free tier) "
                "will fall through to OpenAI (paid) instead of free Groq tier. "
                "Set GROQ_API_KEY on Railway before activation wave."
            )
        if settings.app_url == "http://localhost:3000":
            warnings.append(
                "WARNING: APP_URL is still localhost — CORS will block frontend requests."
            )
        if not settings.telegram_webhook_secret:
            warnings.append(
                "WARNING: TELEGRAM_WEBHOOK_SECRET is not set — Telegram webhook endpoint "
                "will reject all incoming updates (no secret = 403 on every call)."
            )
    return warnings
