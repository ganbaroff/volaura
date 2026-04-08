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
    # ⚠️ PUBLIC anon key for Volaura Supabase project (dwdgzfusjsobnixgyzjk) — PAID plan.
    # Project ref: dwdgzfusjsobnixgyzjk (new paid project, migrated 2026-03-28).
    # Old ref hvykysvdkalkbswmgfut is blocked at startup by RISK-011 guard above.
    # This is intentionally public — RLS enforces all access control.
    # SUPABASE_ANON_JWT is the unintercepted fallback name.
    # If both env vars are missing (Railway interception), the hardcoded default is used.
    _ANON_KEY_DEFAULT: str = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        ".eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZGd6ZnVzanNvYm5peGd5emprIiwicm9sZSI6ImFub24i"
        "LCJpYXQiOjE3NzQ4OTU0MDQsImV4cCI6MjA5MDQ3MTQwNH0"
        ".rbyIBLRONffOKCmfiLJQU_RVEgDmQ5MjUMPj8I8GxOw"
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
    default_locale: str = "az"  # AZ is primary locale; used in server-generated URLs

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

    # Observability — Langfuse: LLM tracing, cost tracking, latency monitoring
    # Free tier: 50k events/month. If keys not set, tracing is silently disabled.
    # Get keys from https://cloud.langfuse.com → Settings → API Keys
    langfuse_public_key: str = ""   # pk-lf-... (from Langfuse dashboard)
    langfuse_secret_key: str = ""   # sk-lf-... (from Langfuse dashboard)
    langfuse_host: str = "https://cloud.langfuse.com"  # EU cloud default; US = us.cloud.langfuse.com

    # NVIDIA NIM — 160+ open-source models, OpenAI-compatible, free tier — added 2026-04-02
    # Base URL: https://integrate.api.nvidia.com/v1 — drop-in OpenAI SDK replacement
    # Swarm routing: nemotron-ultra-253b (reasoning agents) + llama-3.3-70b (speed agents)
    nvidia_api_key: str = ""

    # Stripe (MVP-1)
    # ── KILL SWITCH ──────────────────────────────────────────────────────────────
    # payment_enabled=False (default): paywall bypassed, checkout returns 503.
    # All Stripe infrastructure is wired and tested — flip to True + set keys to activate.
    # Set PAYMENT_ENABLED=true on Railway when ready to charge.
    payment_enabled: bool = False
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id: str = ""  # Monthly subscription price ID (e.g. price_xxx from Stripe dashboard)

    # Transactional email via Resend
    # ── KILL SWITCH ──────────────────────────────────────────────────────────────
    # email_enabled=False (default): no emails sent, silently skipped.
    # Flow: user completes assessment → POST /api/assessment/complete → AURA ready email.
    # Activate: 1) Create Resend account at resend.com  2) Set RESEND_API_KEY on Railway
    #            3) Set EMAIL_ENABLED=true on Railway  4) Verify "noreply@volaura.app" in Resend
    email_enabled: bool = False
    resend_api_key: str = ""  # Set RESEND_API_KEY on Railway

    # Invite gate — controlled beta access (RISK-014)
    # open_signup=True  → anyone can register
    # open_signup=False → invite code required (SAFE DEFAULT — must explicitly set OPEN_SIGNUP=true on Railway to open)
    # beta_invite_code  → set BETA_INVITE_CODE env var on Railway (empty = gate disabled even if open_signup=False)
    open_signup: bool = False
    beta_invite_code: str = ""

    # Google Cloud — Translation LLM for AZ language quality (research 2026-03-31)
    # Primary AZ translation path: Google Translation LLM (Gemini-powered, best quality for agglutinative AZ)
    # Setup: enable Cloud Translation API in GCP console, set GOOGLE_APPLICATION_CREDENTIALS on Railway
    # Free tier: 500k chars/month — covers all Volaura content at current scale
    # If not set, falls back to Gemini direct translation with AZ-specialized prompt
    gcp_project_id: str = ""  # GCP project with Translation API enabled

    # Cron jobs — internal endpoints called by GitHub Actions (not user-facing)
    # Set CRON_SECRET on Railway; same value must be in GitHub Actions secrets.
    # Empty = cron endpoints return 403 (safe default).
    cron_secret: str = ""

    # MindShift — companion ADHD app (cross-product crystal/XP events)
    mindshift_url: str = ""  # e.g. https://mindshift.app — added to CORS in production

    # Sprint E2.D (ADR-006 Option D) — cross-project identity bridge
    # ── supabase_jwt_secret ────────────────────────────────────────────────
    # The JWT signing secret of THIS (shared) Supabase project. Used to mint
    # shared JWTs for users bridged from standalone projects (e.g. MindShift
    # user → shadow user in shared → minted shared JWT → used for /api/character/*).
    # Get from Supabase dashboard → Project Settings → API → JWT Secret.
    # NEVER commit this. Set SUPABASE_JWT_SECRET on Railway.
    # If empty, /api/auth/from_external returns 503 (feature disabled).
    supabase_jwt_secret: str = ""

    # ── external_bridge_secret ─────────────────────────────────────────────
    # Pre-shared secret between VOLAURA backend and MindShift edge function
    # (volaura-bridge-proxy). MindShift edge function passes this as
    # X-Bridge-Secret header when calling /api/auth/from_external. Only the
    # edge function knows this value — protects against unauthenticated
    # clients calling the bridge endpoint to mint JWTs for arbitrary emails.
    # Generate with: python -c "import secrets; print(secrets.token_urlsafe(48))"
    # Set EXTERNAL_BRIDGE_SECRET on both Railway (VOLAURA) and MindShift edge
    # function environment. Rotate together if either side is compromised.
    external_bridge_secret: str = ""

    # BrandedBy — AI video generation
    did_api_key: str = ""  # D-ID API key (Phase 1: Lite plan $5.90/mo)
    fal_api_key: str = ""  # fal.ai API key — MuseTalk + Kling LipSync (DSP winner)

    # Vertex AI — enterprise LLM SLA upgrade (Express API key — $100/mo budget cap)
    # Use: genai.Client(vertexai=True, api_key=vertex_api_key) — NOT project/location ADC
    # Fallback chain: Vertex Express → AI Studio Gemini → Groq → OpenAI
    vertex_api_key: str = ""  # AQ.Ab8... format Express key

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
            "https://modest-happiness-production.up.railway.app",  # Production Railway backend
        ]
        for k in known:
            if k not in origins:
                origins.append(k)
        # MindShift cross-product integration — set MINDSHIFT_URL on Railway
        if self.mindshift_url and self.mindshift_url not in origins:
            origins.append(self.mindshift_url)
        return origins


settings = Settings()


def assert_production_ready() -> None:
    """Raise RuntimeError for settings that will cause silent failures in production.

    Called at startup lifespan. Fails the process early rather than serving broken
    responses (e.g., CORS blocking all requests because APP_URL is still localhost).

    RISK-011 check fires on ALL environments — data loss from wrong DB is not
    limited to production. All other checks are production-only.
    """
    # RISK-011: Old Supabase project guard — fires on ALL envs (not production-only).
    # If SUPABASE_URL still points to old free-tier project, writes go to wrong DB.
    # Assessments, AURA scores, and user data will be silently lost in ANY environment.
    OLD_PROJECT_REFS = ("hvykysvdkalkbswmgfut",)
    for old_ref in OLD_PROJECT_REFS:
        if old_ref in settings.supabase_url:
            raise RuntimeError(
                f"STARTUP BLOCKED: SUPABASE_URL still points to old project ({old_ref}). "
                f"Update Railway env var to https://dwdgzfusjsobnixgyzjk.supabase.co"
            )

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
    # RISK-M01: LLM cost spiral guard — Gemini without Groq falls to paid OpenAI.
    # At activation wave (110 users/hr × 8 questions), Gemini 15 RPM free tier saturates
    # in 5 minutes. Without Groq (14,400 req/day free), cost falls to OpenAI at ~$240/day.
    if settings.gemini_api_key and not settings.groq_api_key:
        errors.append(
            "GROQ_API_KEY is not set — Gemini rate-limit events will fall to paid OpenAI "
            "(est. $240/day at activation wave). Set GROQ_API_KEY on Railway before launch."
        )
    # RISK-N01: Telegram secret — WARNING only (not hard fail).
    # Without secret: bot accepts all Telegram updates (no signature verification).
    # With secret: Telegram adds X-Telegram-Bot-Api-Secret-Token header to every update.
    # Security risk without secret is LOW (CEO_CHAT_ID filter is still enforced).
    # Hard fail removed: app must start even without Telegram fully configured.
    # RISK-N01: Telegram webhook secret guard — fail-closed in production.
    # Without secret: webhook accepts all POST requests (no Telegram signature verification).
    # CEO_CHAT_ID filter still limits who can trigger bot actions, but any attacker can spam
    # the endpoint and exhaust Gemini quota or flood ceo_inbox.
    if not settings.telegram_webhook_secret:
        errors.append(
            "TELEGRAM_WEBHOOK_SECRET is not set — Telegram webhook endpoint accepts all "
            "incoming requests without signature verification. Set TELEGRAM_WEBHOOK_SECRET "
            "on Railway to harden against spam and quota exhaustion."
        )
    # RISK-N02: Stripe webhook signature guard when payment is active.
    # If payment_enabled=True but webhook secret is missing, unsigned webhook events are
    # accepted — an attacker can POST fake subscription.created and get free Pro access.
    if settings.payment_enabled and not settings.stripe_webhook_secret:
        errors.append(
            "STRIPE_WEBHOOK_SECRET is not set but PAYMENT_ENABLED=True — webhook endpoint "
            "accepts unsigned Stripe events. Attacker can grant free Pro subscriptions. "
            "Set STRIPE_WEBHOOK_SECRET on Railway before enabling payments."
        )
    # RISK-011: Old Supabase project guard — prevent split writes after migration.
    # If SUPABASE_URL still points to the old free-tier project, writes go to the wrong
    # database. Assessments, AURA scores, and user data will be silently lost.
    # New project ref: dwdgzfusjsobnixgyzjk (paid plan, active since 2026-03-28).
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
        if not settings.sentry_dsn:
            warnings.append(
                "WARNING: SENTRY_DSN not set — production errors will not be tracked in Sentry."
            )
    return warnings
