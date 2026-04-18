# Content Pipeline Handoff — Atlas / Claude Code

**Created:** 2026-04-12
**Author:** Atlas (Cowork session)
**Priority:** HIGH — CEO directive: "они вечно простаивают, хотя могу пахать весь день"
**Goal:** Connect 51 idle PR/marketing agent skills to real LLM execution via a content pipeline

---

## Problem

The swarm has 51 agent skill files (`memory/swarm/skills/*.md`) but they're injected as ~500 char snippets into prompts via keyword matching (`autonomous_run.py` → `PerspectiveRegistry`). The content/PR agents (Communications Strategist, Cultural Intelligence, Content Formatter, LinkedIn Creator, PR Media, Promotion Agency, Community Manager, Behavioral Nudge) generate proposals that land in `proposals.json` — but nobody executes them.

**Root cause:** No pipeline connects skill files → LLM calls → formatted output → Telegram delivery.

## Solution

Create `packages/swarm/content_pipeline.py` — a 6-step DAG using the existing `Orchestrator` + `AgentTask` pattern from `packages/swarm/orchestrator.py`.

---

## Architecture

```
CEO idea (text)
    │
    ▼
┌─────────────────────────────────┐
│ STEP 1: Communications Strategist │  ← memory/swarm/skills/communications-strategist.md
│         Creates Strategic Brief    │     Full skill text as system prompt
│         Output: JSON brief         │
└──────────┬──────────────────────┘
           ▼
┌─────────────────────────────────┐
│ STEP 2: Cultural Intelligence     │  ← memory/swarm/skills/cultural-intelligence-strategist.md
│         AZ/CIS Audit on brief     │     depends_on: ["strategist"]
│         Output: annotated brief    │
└──────────┬──────────────────────┘
           ▼
┌─────────────────────────────────┐
│ STEP 3: Content Generation        │  ← Uses SPARK/CORTEX copywriter roles
│         Writes all content pieces  │     depends_on: ["cultural_audit"]
│         Reads: tone-rules.md       │     One LLM call per piece
│         Output: draft pieces[]     │
└──────────┬──────────────────────┘
           ▼
┌─────────────────────────────────┐
│ STEP 4: Content Formatter         │  ← memory/swarm/skills/content-formatter.md
│         5 blocks per piece         │     depends_on: ["generation"]
│         POST_CLEAN, TELEGRAM_HTML, │
│         EMAIL_HTML, CTA, IMAGE     │
└──────────┬──────────────────────┘
           ▼
┌─────────────────────────────────┐
│ STEP 5: Quality Gate              │  ← .claude/skills/content-factory/references/tone-rules.md
│         Anti-AI filter (27 words)  │     depends_on: ["formatter"]
│         Constitution 5 Laws        │     BLOCKS if any check fails
│         Tinkoff benchmark          │
└──────────┬──────────────────────┘
           ▼
┌─────────────────────────────────┐
│ STEP 5.5: TTS Voice-over (04-13)  │  ← packages/swarm/tts.py
│         Azure AZ / ElevenLabs EN+RU│     depends_on: ["quality_gate"]
│         Writes WAV to public/voice │     Sets piece.audio_path
└──────────┬──────────────────────┘
           ▼
┌─────────────────────────────────┐
│ STEP 6: Video Render (NEW 04-13)  │  ← packages/remotion/ (@volaura/remotion)
│         For pieces where          │     depends_on: ["tts"]
│         format ∈ {tiktok_az,       │     Writes MP4 / PNG to out/
│         linkedin_carousel}         │     Reads piece.audio_path → <Audio>
│                                    │     Reads .captions.json if present
└──────────┬──────────────────────┘
           ▼
┌─────────────────────────────────┐
│ STEP 7: Telegram Delivery         │  ← packages/swarm/telegram_ambassador.py
│         Send each piece to CEO     │     depends_on: ["video_render"]
│         Text < 4096 chars          │
│         Videos as file attachments │     uses piece.media_path if present
└──────────┬──────────────────────┘
           ▼
┌─────────────────────────────────┐
│ STEP 8: Postiz Scheduling (04-13) │  ← docs/ops/postiz-deployment-handoff.md
│         POST to Postiz API         │     depends_on: ["telegram_delivery"]
│         Schedule to LinkedIn / X / │     One POST per (piece × platform)
│         TikTok / IG / YouTube      │     Idempotent dedupeKey per slug
└─────────────────────────────────┘
```

> **2026-04-13 UPDATE — Step 6 Video Render package is ready.**
> Cowork scaffolded `packages/remotion/` (Remotion 4.0.448, React 18, typecheck green).
> Two compositions ready with real content from `docs/content/weekly-plans/2026-04-13.md`:
- `TikTokAZ` — 1080×1920, 45s (Post #2 — "13 ixtisaslaşdırılmış perspektiv var")
> - `LinkedInCarousel` — 1080×1350, 24s / 8 PNG frames (Post #6 — "I gave AI full control of my startup")
>
> Theme tokens in `packages/remotion/src/theme.ts` enforce Constitution v1.7:
> NEVER RED (errors = `#D4B4FF` purple), max 800ms spring animations, one primary CTA per frame.
>
> Atlas wiring task — add to `content_pipeline.py` between quality_gate and telegram:
> ```python
> # Step 6 — Video Render
> if piece.format in {"tiktok_az", "linkedin_carousel"}:
>     comp_id = "TikTokAZ" if piece.format == "tiktok_az" else "LinkedInCarousel"
>     out = f"out/{piece.slug}.mp4"
>     subprocess.run(
>         ["pnpm", "--filter", "@volaura/remotion", "render", "--", comp_id, out],
>         check=True,
>     )
>     piece.media_path = out
> ```
> Telegram Ambassador (Step 7) already handles file attachments — just needs to
> prefer `piece.media_path` over text when present.

> **2026-04-13 UPDATE — Step 5.5 TTS module is ready.**
> `packages/swarm/tts.py` ships with `synthesize(text, lang, out_path, gender)`.
> Routing: AZ → Azure (`az-AZ-BabekNeural` / `az-AZ-BanuNeural`), EN/RU → ElevenLabs
> Multilingual v2 with PCM 22.05kHz output wrapped in RIFF WAV. Output is
> Whisper-friendly so Step 6 can transcribe to word-level captions immediately
> via `pnpm --filter @volaura/remotion transcribe -- voiceover.wav`.
>
> Atlas wiring (between quality_gate and video_render):
> ```python
> from packages.swarm.tts import synthesize
> if piece.has_voiceover:
>     out = Path(f"apps/web/public/voiceovers/{piece.slug}.wav")
>     synthesize(piece.script, lang=piece.lang, out_path=out)
>     piece.audio_path = f"voiceovers/{piece.slug}.wav"  # relative for staticFile()
> ```
> Then video_render passes `data.audio = piece.audio_path` into the Remotion
> composition's `defaultProps`.

> **2026-04-13 UPDATE — Step 8 Postiz handoff written.**
> See `docs/ops/postiz-deployment-handoff.md` for full deployment plan, env vars
> (`POSTIZ_API_URL`, `POSTIZ_API_KEY`), and acceptance criteria. Atlas client
> (`packages/swarm/postiz_client.py`) is the next-up build — Postiz infra needs
> Railway provision + CEO OAuth before client work starts.

---

## File: `packages/swarm/content_pipeline.py`

### Key design decisions

1. **Use Orchestrator + AgentTask** — already built, DAG-aware, dependency injection works:
   ```python
   from swarm.orchestrator import Orchestrator, AgentTask
   ```

2. **LLM provider hierarchy** (from Constitution):
   ```
   Cerebras Qwen3-235B (primary)
   → Ollama/local qwen3:8b (zero cost)
   → NVIDIA NIM (backup)
   → Gemini Flash (last resort)
   ```
   NEVER use Claude/Anthropic as swarm agent.

3. **Each step = one AgentTask** where `runner` function:
   - Reads the FULL skill markdown (not 500 chars — the ENTIRE file)
   - Builds a system prompt from the skill
   - Calls LLM with the skill as system + step input as user message
   - Parses structured JSON output

4. **Skill files loaded FULLY** — this is the architectural fix:
   ```python
   def load_skill(skill_name: str) -> str:
       path = project_root / "memory" / "swarm" / "skills" / f"{skill_name}.md"
       return path.read_text(encoding="utf-8")
   ```

### Runner function signature

```python
async def content_agent_runner(agent_id: str, input_data: dict) -> dict:
    """Run one content agent step.
    
    agent_id maps to a skill file + system prompt template.
    input_data contains the step's input + injected context from dependencies.
    """
    skill_text = load_skill(AGENT_SKILL_MAP[agent_id])
    
    # Build prompt
    system = f"You are {agent_id}. Follow these instructions exactly:\n\n{skill_text}"
    user = json.dumps(input_data, ensure_ascii=False)
    
    # Call LLM (try providers in order)
    response = await call_llm(system, user, response_format="json")
    
    return json.loads(response)
```

### Agent-to-skill mapping

```python
AGENT_SKILL_MAP = {
    "strategist": "communications-strategist",
    "cultural_audit": "cultural-intelligence-strategist", 
    "content_gen": None,  # Uses inline SPARK/CORTEX prompts
    "formatter": "content-formatter",
    "quality_gate": None,  # Uses tone-rules.md as reference
    "delivery": None,  # Uses telegram bot SDK directly
}
```

### DAG setup

```python
async def run_content_pipeline(idea: str, platforms: list[str] | None = None) -> dict:
    orch = Orchestrator(runner=content_agent_runner, run_id=f"content-{timestamp}")
    
    orch.add_task(AgentTask(
        "strategist", "strategist",
        {"idea": idea, "platforms": platforms or ["tiktok", "linkedin_en", "linkedin_az"]}
    ))
    
    orch.add_task(AgentTask(
        "cultural_audit", "cultural_audit",
        {"brief": "injected_from_strategist"},
        depends_on=["strategist"]
    ))
    
    orch.add_task(AgentTask(
        "content_gen", "content_gen",
        {"audited_brief": "injected_from_cultural_audit"},
        depends_on=["cultural_audit"]
    ))
    
    orch.add_task(AgentTask(
        "formatter", "formatter",
        {"drafts": "injected_from_content_gen"},
        depends_on=["content_gen"]
    ))
    
    orch.add_task(AgentTask(
        "quality_gate", "quality_gate",
        {"formatted": "injected_from_formatter"},
        depends_on=["formatter"]
    ))
    
    orch.add_task(AgentTask(
        "delivery", "delivery",
        {"approved": "injected_from_quality_gate"},
        depends_on=["quality_gate"]
    ))
    
    results = await orch.run_all(timeout=600)
    return results
```

### LLM call function

```python
async def call_llm(system: str, user: str, response_format: str = "json") -> str:
    """Call LLM using provider hierarchy. Returns raw text."""
    
    providers = [
        ("cerebras", "qwen-3-235b"),          # Primary — 2000+ tok/s
        ("ollama", "qwen3:8b"),                # Zero cost local
        ("nvidia", "meta/llama-3.3-70b"),      # Backup
        ("gemini", "gemini-2.5-flash"),         # Last resort
    ]
    
    for provider_name, model in providers:
        try:
            return await _call_provider(provider_name, model, system, user)
        except Exception as e:
            logger.warning(f"Provider {provider_name} failed: {e}")
            continue
    
    raise RuntimeError("All LLM providers failed")
```

Use the existing provider infrastructure from `packages/swarm/providers/` — check what's already registered in `ProviderRegistry` before writing new provider code.

---

## File: `packages/swarm/telegram_ambassador.py` — Additions

Add a `/content <idea>` command handler:

```python
@bot.command("content")
async def handle_content(update, context):
    """CEO sends idea → pipeline runs → results delivered as messages."""
    idea = " ".join(context.args)
    if not idea:
        await update.message.reply_text("Usage: /content <your idea>")
        return
    
    await update.message.reply_text(f"🏭 Pipeline started: {idea[:50]}...")
    
    results = await run_content_pipeline(idea)
    
    # Send each approved piece as separate Telegram message
    delivery_task = results.get("delivery")
    if delivery_task and delivery_task.result:
        for piece in delivery_task.result.get("pieces", []):
            text = piece.get("TELEGRAM_HTML") or piece.get("POST_CLEAN", "")
            if len(text) > 4096:
                text = text[:4090] + "..."
            await update.message.reply_text(text, parse_mode="HTML")
```

---

## Quality Gate Implementation (Step 5)

The quality gate is NOT an LLM call — it's programmatic:

```python
ANTI_AI_WORDS = [
    "excited to announce", "leverage", "utilize", "innovative", 
    "passionate about", "ecosystem", "streamline", "robust", 
    "scalable", "empower", "disrupt", "holistic", "paradigm",
    "at the end of the day", "it's worth noting", "let's dive in",
    "without further ado", "game-changer", "cutting-edge", 
    "state-of-the-art", "synergy", "circle back", "low-hanging fruit"
]

def quality_check(piece: dict) -> tuple[bool, list[str]]:
    """Returns (passed, list_of_failures)."""
    failures = []
    text = piece.get("POST_CLEAN", "").lower()
    
    # Anti-AI filter
    for word in ANTI_AI_WORDS:
        if word in text:
            failures.append(f"Anti-AI: found '{word}'")
    
    # Constitution Law 1: Never Red
    if "red" in piece.get("IMAGE_PROMPT", "").lower():
        failures.append("Constitution Law 1: red in IMAGE_PROMPT")
    
    # Real number check
    import re
    if not re.search(r'\d+', text):
        failures.append("No real number found in text")
    
    # CTA check
    if not piece.get("CTA"):
        failures.append("Missing CTA")
    
    return len(failures) == 0, failures
```

---

## Acceptance Criteria

```gherkin
DONE when:
  1. PASS: `python -m packages.swarm.content_pipeline --idea "13 perspectives, zero standup"` 
     produces 3+ formatted content pieces (TikTok, LinkedIn EN, LinkedIn AZ)
  2. PASS: Each piece has all 5 format blocks (POST_CLEAN, TELEGRAM_HTML, EMAIL_HTML, CTA, IMAGE_PROMPT)
  3. PASS: Quality gate catches anti-AI words and blocks pieces that fail
  4. PASS: AZ and EN versions are structurally different (not translations)
  5. PASS: `/content <idea>` in Telegram delivers pieces to CEO chat
  6. PASS: Full pipeline completes in < 120 seconds
  7. PASS: No Claude/Anthropic models used as agents
  8. PASS (video, added 04-13): pieces with format ∈ {tiktok_az, linkedin_carousel}
     render to MP4/PNG via `@volaura/remotion` and piece.media_path is set
  9. PASS (video): Telegram delivery attaches media_path file when present instead of text
 10. PASS (TTS, added 04-13): pieces with has_voiceover=True get a WAV at
     apps/web/public/voiceovers/<slug>.wav and piece.audio_path is set
 11. PASS (TTS): AZ pieces use Azure (az-AZ-*Neural), EN/RU pieces use ElevenLabs;
     no language ever crosses providers
 12. PASS (Postiz, added 04-13): each approved piece is POSTed to Postiz with
     a sha256(platform+slug+week) dedupeKey; re-runs do NOT create duplicates
```

---

## Files to create/modify

| Action | File | What |
|--------|------|------|
| CREATE | `packages/swarm/content_pipeline.py` | Main pipeline (now 7-step DAG after 04-13 video render addition) |
| MODIFY | `packages/swarm/telegram_ambassador.py` | Add `/content` command + prefer `piece.media_path` attachment when present |
| MODIFY | `packages/swarm/autonomous_run.py` | Add `--mode=content-batch` mode |
| CREATE | `packages/swarm/content_prompts.py` | Step-specific prompt templates (SPARK/CORTEX roles, quality gate criteria) |
| DONE   | `packages/remotion/` | Video render package (scaffolded 2026-04-13 by Cowork — Remotion 4.0.448, 2 compositions, typecheck green) |
| DONE   | `packages/swarm/tts.py` | TTS module (scaffolded 2026-04-13 — Azure AZ + ElevenLabs EN/RU, WAV out) |
| CREATE | `packages/swarm/postiz_client.py` | Postiz REST client + dedupeKey logic (after Postiz is provisioned per `docs/ops/postiz-deployment-handoff.md`) |

---

## Existing code to REUSE (do not reinvent)

| What | Where | How to use |
|------|-------|------------|
| DAG orchestrator | `packages/swarm/orchestrator.py` | `Orchestrator` + `AgentTask` with `depends_on` |
| Shared memory | `packages/swarm/shared_memory.py` | `post_result()` / `get_context()` between steps |
| Provider registry | `packages/swarm/providers/` | Check existing providers before adding new ones |
| Skill files (full text) | `memory/swarm/skills/*.md` | Load ENTIRE file as system prompt — NOT 500 char snippet |
| Telegram bot | `packages/swarm/telegram_ambassador.py` | Add handler, reuse existing bot instance |
| Video generation | `packages/swarm/zeus_video_skill.py` | `ZeusVideoSkill.generate()` for talking-head videos |
| Tone rules | `.claude/skills/content-factory/references/tone-rules.md` | Quality gate reference |
| Social formats | `.claude/skills/content-factory/references/social-formats.md` | Generation templates |

---

## What NOT to do

- Do NOT use Claude/Anthropic as swarm agents
- Do NOT create new provider wrappers if they exist in `packages/swarm/providers/`
- Do NOT truncate skill files to 500 chars — load the FULL markdown
- Do NOT make AZ a translation of EN — they are different pieces
- Do NOT skip the quality gate for "speed"
- Do NOT hardcode platform list — let CEO 