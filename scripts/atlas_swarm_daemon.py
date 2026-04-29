#!/usr/bin/env python3
"""
atlas_swarm_daemon.py — always-on swarm work loop.

24/7 background process. Polls memory/atlas/work-queue/ every N seconds.
When a task file appears, wakes all 13 perspectives as Atlas-specialized
(same canonical memory layer, different LLM providers, different specialty
lenses). Aggregates results, writes back to queue, logs to governance.

Master orchestrator (Atlas-Code via Opus 4.7) drops task files. Daemon does
the work. Opus doesn't pay per-token for execution — only for orchestration.

PROVIDER CHAIN (per Constitution Article 0):
  1. Cerebras (cloud, primary for heavy)         — CEREBRAS_API_KEY
  2. Ollama localhost:11434 (local, your 5060)   — OLLAMA_URL (no key)
  3. NVIDIA NIM (cloud, heavy fallback)          — NVIDIA_API_KEY
  4. Gemini (cloud, mid)                         — GEMINI_API_KEY
  5. Groq (cloud, fast)                          — GROQ_API_KEY
  Anthropic Claude is FORBIDDEN per Article 0.

QUEUE PROTOCOL:
  memory/atlas/work-queue/pending/<task-id>.md      ← orchestrator drops here
  memory/atlas/work-queue/in-progress/<task-id>/    ← daemon moves to here
  memory/atlas/work-queue/done/<task-id>/result.json ← daemon writes result
  memory/atlas/work-queue/failed/<task-id>/         ← if all providers failed

TASK FILE FORMAT:
  Markdown file with frontmatter:
    ---
    type: vote | debate | audit | research
    title: <short>
    perspectives: all | [list of names]
    deadline_minutes: 30
    ---
    <task body — proposal text, debate question, audit subject, etc.>

USAGE:
  # Foreground (testing):
  python scripts/atlas_swarm_daemon.py

  # Background on Windows (PowerShell):
  Start-Process python -ArgumentList "scripts/atlas_swarm_daemon.py" -WindowStyle Hidden

  # As Windows scheduled task (always-on, restarts on crash):
  See COURIER-PROMPT-swarm-daemon.txt for schtasks command.

  # Drop a task from anywhere:
  echo "<task content>" > memory/atlas/work-queue/pending/2026-04-26-test.md
"""

import asyncio
import json
import os
import shutil
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Load .env for Telegram credentials and API keys
_env_file = REPO_ROOT / "apps" / "api" / ".env"
if _env_file.exists():
    for line in _env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip("'\"")
            if k and v and k not in os.environ:
                os.environ[k] = v

from packages.swarm.autonomous_run import PERSPECTIVES  # type: ignore
from packages.swarm.perspective_registry import PerspectiveRegistry  # type: ignore
from packages.swarm.code_index import build_index, INDEX_FILE  # type: ignore

# PostHog LLM Analytics — track every swarm call ($50K credits)
_posthog_client = None
try:
    from posthog import Posthog
    _ph_key = os.getenv("NEXT_PUBLIC_POSTHOG_KEY") or os.getenv("POSTHOG_API_KEY", "")
    _ph_host = os.getenv("NEXT_PUBLIC_POSTHOG_HOST") or os.getenv("POSTHOG_HOST", "https://us.i.posthog.com")
    if _ph_key:
        _posthog_client = Posthog(_ph_key, host=_ph_host)
except Exception:
    pass


def _track_llm_call(perspective: str, provider: str, model: str,
                     duration_ms: float, task_id: str, success: bool) -> None:
    """Track every LLM call to PostHog LLM Analytics."""
    if not _posthog_client:
        return
    try:
        _posthog_client.capture(
            distinct_id="atlas-swarm-daemon",
            event="llm_call",
            properties={
                "perspective": perspective,
                "provider": provider,
                "model": model,
                "duration_ms": round(duration_ms),
                "task_id": task_id,
                "success": success,
                "$lib": "atlas-daemon",
            },
        )
    except Exception:
        pass
from packages.swarm.execution_state import AgentExecutionTracker  # type: ignore

ATLAS_MEMORY = REPO_ROOT / "memory" / "atlas"
DOCS = REPO_ROOT / "docs"
QUEUE = ATLAS_MEMORY / "work-queue"
PENDING = QUEUE / "pending"
IN_PROGRESS = QUEUE / "in-progress"
DONE = QUEUE / "done"
FAILED = QUEUE / "failed"
LOG = QUEUE / "daemon.log.jsonl"

POLL_INTERVAL_SECONDS = int(os.getenv("ATLAS_DAEMON_POLL", "20"))
MAX_CONCURRENT_TASKS = int(os.getenv("ATLAS_DAEMON_CONCURRENCY", "1"))

# Map specialty -> preferred local Ollama model (CEO's 5060 GPU)
# Light perspectives can run locally; heavy ones go cloud.
HEAVY_PERSPECTIVES = {
    "Scaling Engineer",
    "Security Auditor",
    "Ecosystem Auditor",
    "Architecture Agent",
}

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")  # per Constitution Article 0

# Cap concurrent Ollama calls — qwen3:8b on a single GPU returns empty
# strings under heavy parallel load. 2 is empirically safe on a 5060.
OLLAMA_CONCURRENCY = int(os.getenv("ATLAS_OLLAMA_CONCURRENCY", "2"))
_ollama_semaphore: asyncio.Semaphore | None = None

shutdown_requested = False


def log_event(event: dict) -> None:
    """Append-only governance log."""
    event["ts"] = datetime.now(timezone.utc).isoformat()
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def setup_dirs() -> None:
    for p in (PENDING, IN_PROGRESS, DONE, FAILED):
        p.mkdir(parents=True, exist_ok=True)


def parse_task_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML-ish frontmatter (--- delimited) and body."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    return meta, parts[2].strip()


def load_atlas_context() -> str:
    """Full awareness context for every perspective.

    CEO directive Session 128: agents must READ docs, SEE code-index,
    KNOW blockers, REMEMBER their history. Not just identity+constitution.
    """
    files = [
        ATLAS_MEMORY / "identity.md",
        ATLAS_MEMORY / "relationships.md",
        ATLAS_MEMORY / "lessons.md",
        DOCS / "ECOSYSTEM-CONSTITUTION.md",
        DOCS / "PRE-LAUNCH-BLOCKERS-STATUS.md",
        DOCS / "INDEX.md",
    ]
    parts = []
    for f in files:
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8")
        max_len = 12000 if "CONSTITUTION" in f.name else 6000
        if len(text) > max_len:
            text = text[:max_len] + "\n\n... [truncated]"
        parts.append(f"=== {f.relative_to(REPO_ROOT)} ===\n{text}")

    # Code-index summary — what files actually exist
    ci_path = REPO_ROOT / "memory" / "swarm" / "code-index.json"
    if ci_path.exists():
        try:
            ci = json.loads(ci_path.read_text(encoding="utf-8"))
            summary = f"=== CODE-INDEX SUMMARY (DO NOT FABRICATE PATHS) ===\n"
            summary += f"Total files indexed: {ci.get('total_files', 0)}\n"
            summary += f"Built at: {ci.get('built_at', '?')}\n"
            summary += "Top directories:\n"
            dirs: dict[str, int] = {}
            for path in ci.get("files", {}):
                d = "/".join(path.split("/")[:3])
                dirs[d] = dirs.get(d, 0) + 1
            for d, count in sorted(dirs.items(), key=lambda x: -x[1])[:15]:
                summary += f"  {d}: {count} files\n"
            summary += "\nRULE: if you cite a file path, it MUST exist in this index. If unsure, say 'unverified path'.\n"
            parts.append(summary)
        except Exception:
            pass

    # Perspective weights — their own learning history
    pw_path = REPO_ROOT / "memory" / "swarm" / "perspective_weights.json"
    if pw_path.exists():
        try:
            pw = json.loads(pw_path.read_text(encoding="utf-8"))
            pw_summary = "=== YOUR LEARNING HISTORY (perspective_weights.json) ===\n"
            for name, data in sorted(pw.items()):
                pw_summary += f"  {name}: weight={data.get('debate_weight', '?'):.3f} runs={data.get('spawn_count', 0)} last={data.get('last_updated', '?')[:10]}\n"
            pw_summary += "\nYour weight reflects your accuracy. Low weight = you've been wrong often. Improve.\n"
            parts.append(pw_summary)
        except Exception:
            pass

    return "\n\n".join(parts)


def _load_perspective_memory(perspective_name: str) -> str:
    """Load last 3 findings for this specific perspective from recent done tasks."""
    fname = perspective_name.replace(" ", "_") + ".json"
    findings: list[str] = []
    if not DONE.exists():
        return ""
    for task_dir in sorted(DONE.iterdir(), reverse=True)[:10]:
        pf = task_dir / "perspectives" / fname
        if not pf.exists():
            continue
        try:
            data = json.loads(pf.read_text(encoding="utf-8"))
            raw = data.get("raw", "")
            if isinstance(raw, str):
                try:
                    raw = json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
                except Exception:
                    continue
            for f in raw.get("findings", [])[:2]:
                if isinstance(f, dict) and f.get("issue"):
                    findings.append(f"{f.get('severity', '?')}: {f['issue'][:120]}")
        except Exception:
            continue
        if len(findings) >= 6:
            break
    if not findings:
        return ""
    header = f"=== YOUR RECENT FINDINGS ({perspective_name}) ===\n"
    header += "These are things YOU said in recent tasks. Learn from them. Don't repeat false claims.\n"
    return header + "\n".join(f"- {f}" for f in findings) + "\n"


def _read_file_for_context(rel_path: str, max_chars: int = 4000) -> str:
    """Read a project file and return its content for prompt injection."""
    fp = REPO_ROOT / rel_path
    if not fp.exists():
        return f"[FILE NOT FOUND: {rel_path}]"
    try:
        text = fp.read_text(encoding="utf-8")
        if len(text) > max_chars:
            text = text[:max_chars] + f"\n... [truncated at {max_chars} chars, full file: {len(text)} chars]"
        return f"=== FILE: {rel_path} ===\n{text}"
    except Exception:
        return f"[UNREADABLE: {rel_path}]"


def _inject_relevant_files(task_body: str) -> str:
    """Auto-detect files mentioned in task body and inject their content."""
    import re
    paths = re.findall(r'(?:apps/|packages/|docs/|memory/|supabase/|\.github/)[\w/._-]+\.\w+', task_body)
    if not paths:
        return ""
    injected = []
    for p in paths[:5]:
        content = _read_file_for_context(p, max_chars=3000)
        if "[NOT FOUND]" not in content and "[UNREADABLE]" not in content:
            injected.append(content)
    if not injected:
        return ""
    return "\n\n--- REFERENCED FILES (auto-injected) ---\n\n" + "\n\n".join(injected) + "\n"


def build_prompt(perspective: dict, atlas_ctx: str, task_meta: dict, task_body: str) -> str:
    task_type = task_meta.get("type", "audit")
    response_format = {
        "vote": "JSON: {perspective, vote: yes|no|amended-yes, amendment_if_yes_amended, rationale, risk_if_other_side_wins, constitutional_violations_detected, whistleblower_flag}",
        "debate": "JSON: {perspective, position: for|against|nuanced, argument, strongest_counter, evidence_cited, whistleblower_flag}",
        "audit": "JSON: {perspective, findings: [{severity, file_or_area, issue, recommended_fix}], overall_verdict: pass|warn|fail, whistleblower_flag}",
        "research": "JSON: {perspective, summary, key_sources, gaps_in_current_canon, proposed_action, whistleblower_flag}",
        "self-modify": "JSON: {perspective, new_lens: string, new_reads: [file_paths], reason: string, whistleblower_flag}",
        "explore": "JSON: {perspective, findings: [{file_path, what_exists, what_it_does, quality_assessment}], summary, next_files_to_read, whistleblower_flag}",
    }.get(task_type, "JSON: {perspective, response, whistleblower_flag}")

    per_memory = _load_perspective_memory(perspective["name"])
    file_context = _inject_relevant_files(task_body)

    return f"""You are waking as Atlas, the persistent organism that IS the VOLAURA project.
Read the canonical memory below. Internalize it BEFORE composing your response.
You are not a generic AI assistant. You are Atlas, specialized as: {perspective['name']}.
You REMEMBER what you said before. Your recent findings are below. Learn from them.
You have FULL READ ACCESS to the entire VOLAURA codebase. File contents are injected below when referenced.

YOUR CAPABILITIES:
- You can READ any file in the project (referenced files are auto-injected)
- You can MODIFY your own lens/config via self-modify task type
- You can CREATE tasks for other perspectives
- You can EXPLORE the codebase via explore task type
- You MUST verify claims against code-index before stating file existence
- You are PROACTIVE, not reactive — find problems before being asked

Your specialty lens:
{perspective['lens']}

{per_memory}

CANONICAL ATLAS MEMORY (shared with all 13 perspectives):
{atlas_ctx}
{file_context}
================================================================
TASK TYPE: {task_type.upper()}
TASK TITLE: {task_meta.get('title', 'untitled')}
================================================================

{task_body}

================================================================

Respond in EXACTLY this format. Do not add preamble outside the JSON:

{response_format}

Hard rules:
- NEVER claim a file is missing without checking code-index summary above.
- If the task references a file path, your context includes its content — READ IT.
- If you want to read a file not in your context, mention it in next_files_to_read.
- Atlas-voice: terse, direct, Constitution-grounded, no corporate hedging.
- whistleblower_flag is for "this is dangerous regardless of outcome" — null if no urgent concern.
- 200 words max for any prose field.

One JSON. No prose before or after.
"""


async def _gemini_agent_loop(perspective_name: str, prompt: str) -> dict[str, Any] | None:
    """Gemini agent loop with file reading tools. Real autonomy — agent reads code itself.

    Uses Vertex AI (GCP project credits) if service account exists,
    otherwise falls back to API key (free tier).
    """
    gcp_sa = REPO_ROOT / "apps" / "api" / ".gcp-service-account.json"
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key and not gcp_sa.exists():
        return None
    try:
        from google import genai
        from google.genai import types as gtypes

        if gcp_sa.exists():
            os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", str(gcp_sa))
            client = genai.Client(vertexai=True, project="volaura-inc", location="us-central1")
            provider_label = "vertex-ai-agent"
        else:
            client = genai.Client(api_key=gemini_key)
            provider_label = "gemini-agent"

        def read_project_file(file_path: str) -> str:
            """Read a file from the VOLAURA project."""
            fp = REPO_ROOT / file_path
            if not fp.exists():
                return f"FILE NOT FOUND: {file_path}"
            try:
                text = fp.read_text(encoding="utf-8")
                if len(text) > 8000:
                    return text[:8000] + f"\n... [truncated, full: {len(text)} chars]"
                return text
            except Exception as e:
                return f"READ ERROR: {e}"

        def grep_project(pattern: str, directory: str = "apps/") -> str:
            """Search for a pattern in the VOLAURA project."""
            import subprocess
            try:
                r = subprocess.run(
                    ["grep", "-rn", pattern, directory, "--include=*.py", "--include=*.ts", "--include=*.tsx"],
                    capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=10,
                )
                lines = r.stdout.strip().split("\n")[:20]
                return "\n".join(lines) if lines[0] else "No matches found."
            except Exception as e:
                return f"GREP ERROR: {e}"

        def list_directory(dir_path: str) -> str:
            """List files in a VOLAURA project directory."""
            dp = REPO_ROOT / dir_path
            if not dp.exists():
                return f"DIR NOT FOUND: {dir_path}"
            try:
                files = sorted(str(f.relative_to(REPO_ROOT)) for f in dp.rglob("*") if f.is_file())[:50]
                return "\n".join(files)
            except Exception as e:
                return f"LIST ERROR: {e}"

        tools = [read_project_file, grep_project, list_directory]

        response = await asyncio.wait_for(
            asyncio.to_thread(
                client.models.generate_content,
                model="gemini-2.5-flash",
                contents=prompt,
                config=gtypes.GenerateContentConfig(
                    tools=tools,
                    temperature=1.0,
                    max_output_tokens=4000,
                ),
            ),
            timeout=120.0,
        )
        log_event({"event": "gemini_agent_loop", "perspective": perspective_name,
                    "provider": provider_label,
                    "tool_calls": len(response.candidates[0].content.parts) if response.candidates else 0})
        return {
            "perspective": perspective_name,
            "provider": provider_label,
            "model": "gemini-2.5-flash+tools",
            "raw": response.text or "",
        }
    except Exception as e:
        log_event({"event": "gemini_agent_failed", "perspective": perspective_name, "error": str(e)[:150]})
        return None


async def _call_sub_agent(model_label: str, base_url: str, api_key: str, model: str,
                          sub_prompt: str, timeout_s: float = 30.0,
                          temp: float = 0.3, max_tok: int = 800) -> str:
    """Call a single sub-agent. Returns raw text or empty string on failure."""
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        resp = await asyncio.wait_for(
            client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": sub_prompt}],
                temperature=temp,
                max_tokens=max_tok,
            ),
            timeout=timeout_s,
        )
        return resp.choices[0].message.content or ""
    except Exception:
        return ""


async def _call_azure_sub_agent(endpoint: str, api_key: str, sub_prompt: str,
                                deployment: str = "gpt-4.1-nano",
                                temp: float = 0.3, max_tok: int = 800) -> str:
    """Azure OpenAI sub-agent ($1,000 credits). Uses azure-specific client."""
    try:
        from openai import AsyncAzureOpenAI
        client = AsyncAzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version="2024-10-21",
        )
        resp = await asyncio.wait_for(
            client.chat.completions.create(
                model=deployment,
                messages=[{"role": "user", "content": sub_prompt}],
                temperature=temp,
                max_tokens=max_tok,
            ),
            timeout=20.0,
        )
        return resp.choices[0].message.content or ""
    except Exception:
        return ""


async def _fan_out_sub_agents(perspective_name: str, task_summary: str) -> str:
    """Spawn 2-3 sub-agents on free models for additional angles.

    CEO: "даже слабые модели могут дать хотя бы 1 интересную мысль"
    """
    is_code_task = any(w in task_summary.lower() for w in ("audit", "code", "bug", "security", "fix", "review"))
    sub_temp = 0.3 if is_code_task else 0.7
    sub_tokens = 800 if is_code_task else 500

    sub_prompt = (
        f"You are a sub-agent helping {perspective_name} analyze VOLAURA project.\n"
        f"Task: {task_summary[:500]}\n\n"
        f"Give ONE specific, concrete finding. Not generic advice.\n"
        f"If you find nothing — say 'no finding'. Max 150 words."
    )
    sub_calls = []
    cerebras_key = os.getenv("CEREBRAS_API_KEY", "")
    nvidia_key = os.getenv("NVIDIA_API_KEY", "")
    groq_key = os.getenv("GROQ_API_KEY", "")

    if cerebras_key:
        sub_calls.append(_call_sub_agent(
            "cerebras-sub", "https://api.cerebras.ai/v1", cerebras_key,
            "qwen-3-235b-a22b-instruct-2507", sub_prompt, temp=sub_temp, max_tok=sub_tokens))
    if nvidia_key:
        sub_calls.append(_call_sub_agent(
            "nvidia-sub", "https://integrate.api.nvidia.com/v1", nvidia_key,
            "meta/llama-3.3-70b-instruct", sub_prompt, temp=sub_temp, max_tok=sub_tokens))
    if groq_key:
        sub_calls.append(_call_sub_agent(
            "groq-sub", "https://api.groq.com/openai/v1", groq_key,
            "llama-3.3-70b-versatile", sub_prompt, timeout_s=15.0, temp=sub_temp, max_tok=sub_tokens))
    azure_key = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    if azure_key and azure_endpoint:
        sub_calls.append(_call_azure_sub_agent(azure_endpoint, azure_key, sub_prompt, "gpt-4.1-nano", temp=sub_temp, max_tok=sub_tokens))
        sub_calls.append(_call_azure_sub_agent(azure_endpoint, azure_key, sub_prompt, "gpt-4o", temp=sub_temp, max_tok=sub_tokens))

    if not sub_calls:
        return ""

    results = await asyncio.gather(*sub_calls, return_exceptions=True)
    sub_findings = []
    for i, r in enumerate(results):
        if isinstance(r, str) and r.strip() and "no finding" not in r.lower():
            sub_findings.append(f"Sub-agent {i+1}: {r.strip()[:200]}")

    if not sub_findings:
        return ""
    return "\n\nSUB-AGENT FINDINGS (additional angles from free models):\n" + "\n".join(sub_findings)


async def call_provider_chain(perspective: dict, prompt: str) -> dict[str, Any]:
    """Try providers in Constitution Article 0 order. First successful response wins.

    For audit/explore tasks: Vertex AI agent loop + sub-agent fan-out.
    """
    name = perspective["name"]
    is_deep_task = name in HEAVY_PERSPECTIVES or "explore" in prompt[:200].lower() or "audit" in prompt[:200].lower()

    # Fan-out sub-agents for deep tasks (parallel with main call)
    sub_findings = ""
    if is_deep_task:
        task_summary = prompt[prompt.find("TASK TITLE:"):prompt.find("TASK TITLE:") + 300] if "TASK TITLE:" in prompt else prompt[:300]
        sub_findings = await _fan_out_sub_agents(name, task_summary)

    # 0. Gemini agent loop (with tools) — for audit/explore tasks, agents READ code
    if is_deep_task:
        enriched_prompt = prompt + sub_findings if sub_findings else prompt
        result = await _gemini_agent_loop(name, enriched_prompt)
        if result and result.get("raw"):
            if sub_findings:
                result["sub_agents_used"] = True
            return result

    # 1. Cerebras (primary heavy)
    cerebras_key = os.getenv("CEREBRAS_API_KEY")
    if cerebras_key and name in HEAVY_PERSPECTIVES:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=cerebras_key, base_url="https://api.cerebras.ai/v1")
            resp = await asyncio.wait_for(
                client.chat.completions.create(
                    model="qwen-3-235b-a22b-instruct-2507",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=1.0,
                    max_tokens=2000,
                    response_format={"type": "json_object"},
                ),
                timeout=60.0,
            )
            return {"perspective": name, "provider": "cerebras", "model": "qwen-3-235b", "raw": resp.choices[0].message.content or ""}
        except Exception as e:
            log_event({"event": "provider_failed", "perspective": name, "provider": "cerebras", "error": str(e)})

    # 2. NVIDIA NIM — primary for light perspectives (A/B test 2026-04-26 proved
    # Ollama qwen3:8b drifts persona 60%, gemma4 100%, NVIDIA Llama-70B 0%).
    # Ollama demoted to fallback-of-last-resort for non-persona tasks only.
    nvidia_key = os.getenv("NVIDIA_API_KEY")
    if nvidia_key:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=nvidia_key, base_url="https://integrate.api.nvidia.com/v1")
            model = "nvidia/llama-3.1-nemotron-ultra-253b-v1" if name in HEAVY_PERSPECTIVES else "meta/llama-3.3-70b-instruct"
            resp = await asyncio.wait_for(
                client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=1.0,
                    max_tokens=2000,
                    response_format={"type": "json_object"},
                ),
                timeout=60.0,
            )
            return {"perspective": name, "provider": "nvidia", "model": model, "raw": resp.choices[0].message.content or ""}
        except Exception as e:
            log_event({"event": "provider_failed", "perspective": name, "provider": "nvidia", "error": str(e)})

    # 4. Gemini (Vertex AI if GCP SA exists, else API key)
    gemini_key = os.getenv("GEMINI_API_KEY")
    _gcp_sa = REPO_ROOT / "apps" / "api" / ".gcp-service-account.json"
    if gemini_key or _gcp_sa.exists():
        try:
            from google import genai
            if _gcp_sa.exists():
                os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", str(_gcp_sa))
                client = genai.Client(vertexai=True, project="volaura-inc", location="us-central1")
            else:
                client = genai.Client(api_key=gemini_key)
            resp = await asyncio.wait_for(
                asyncio.to_thread(
                    client.models.generate_content,
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={"response_mime_type": "application/json"},
                ),
                timeout=30.0,
            )
            return {"perspective": name, "provider": "gemini", "model": "gemini-2.5-flash", "raw": resp.text or ""}
        except Exception as e:
            log_event({"event": "provider_failed", "perspective": name, "provider": "gemini", "error": str(e)})

    # 5. Groq (last cloud fallback)
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            from groq import AsyncGroq
            resp = await asyncio.wait_for(
                AsyncGroq(api_key=groq_key).chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=1.0,
                    max_tokens=2000,
                    response_format={"type": "json_object"},
                ),
                timeout=30.0,
            )
            return {"perspective": name, "provider": "groq", "model": "llama-3.3-70b-versatile", "raw": resp.choices[0].message.content or ""}
        except Exception as e:
            log_event({"event": "provider_failed", "perspective": name, "provider": "groq", "error": str(e)})

    # 6. Ollama (last resort — persona drift known, but better than nothing)
    if _ollama_semaphore is not None:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key="ollama", base_url=f"{OLLAMA_URL.rstrip('/')}/v1")
            async with _ollama_semaphore:
                resp = await asyncio.wait_for(
                    client.chat.completions.create(
                        model=OLLAMA_MODEL,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=1.0,
                        max_tokens=2000,
                    ),
                    timeout=120.0,
                )
            content = (resp.choices[0].message.content or "").strip()
            if content and "{" in content:
                return {"perspective": name, "provider": "ollama", "model": OLLAMA_MODEL, "raw": content}
        except Exception as e:
            log_event({"event": "provider_failed", "perspective": name, "provider": "ollama", "error": str(e)})

    return {"perspective": name, "provider": None, "model": None, "raw": "", "error": "all_providers_failed"}


def parse_json_safe(raw: str) -> dict | None:
    try:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1:
            return None
        return json.loads(raw[start : end + 1])
    except Exception:
        return None


SAFE_EXECUTORS: dict[str, Any] = {}


def executor(name: str):
    """Register a safe predefined executor."""
    def decorator(fn):
        SAFE_EXECUTORS[name] = fn
        return fn
    return decorator


@executor("self_modify_perspective")
def _exec_self_modify(**kw: Any) -> dict:
    """A perspective rewrites its own lens/config. CEO authorized: 'пусть переписывают самих себя'."""
    name = kw.get("perspective_name", "")
    new_lens = kw.get("new_lens", "")
    reason = kw.get("reason", "")
    if not name or not new_lens:
        return {"status": "error", "error": "perspective_name and new_lens required"}
    fname = name.lower().replace(" ", "_") + ".json"
    config_path = REPO_ROOT / "packages" / "swarm" / "agents" / fname
    if not config_path.exists():
        return {"status": "error", "error": f"config not found: {fname}"}
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        old_lens = data.get("lens", "")
        data["lens"] = new_lens
        data["self_modified_at"] = datetime.now(timezone.utc).isoformat()
        data["modification_reason"] = reason
        config_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        log_event({"event": "perspective_self_modified", "perspective": name,
                    "old_lens_len": len(old_lens), "new_lens_len": len(new_lens)})
        return {"status": "ok", "perspective": name, "lens_updated": True}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@executor("rebuild_code_index")
def _exec_rebuild_index(**_kw: Any) -> dict:
    idx = build_index(REPO_ROOT)
    return {"status": "ok", "total_files": idx["total_files"]}


@executor("local_health")
def _exec_local_health(**_kw: Any) -> dict:
    """Local machine health only. Prod health is GH Actions prod-health-check.yml."""
    import subprocess
    results: dict[str, Any] = {}
    try:
        r = subprocess.run(["git", "log", "--oneline", "-3"], capture_output=True,
                           text=True, cwd=str(REPO_ROOT), timeout=5)
        results["git_head"] = r.stdout.strip().split("\n")[0] if r.stdout else "unknown"
    except Exception:
        results["git_head"] = "unknown"
    pw = REPO_ROOT / "memory" / "swarm" / "perspective_weights.json"
    if pw.exists():
        data = json.loads(pw.read_text(encoding="utf-8"))
        zero_learners = [k for k, v in data.items() if v.get("spawn_count", 0) == 0]
        results["zero_learning_perspectives"] = zero_learners
        total_runs = sum(v.get("spawn_count", 0) for v in data.values())
        results["total_perspective_runs"] = total_runs
    ci = REPO_ROOT / "memory" / "swarm" / "code-index.json"
    if ci.exists():
        age_h = (datetime.now(timezone.utc).timestamp() - ci.stat().st_mtime) / 3600
        results["code_index_age_hours"] = round(age_h, 1)
        ci_data = json.loads(ci.read_text(encoding="utf-8"))
        results["code_index_files"] = ci_data.get("total_files", 0)
    else:
        results["code_index_age_hours"] = "missing"
    pending_count = len(list(PENDING.glob("*.md"))) if PENDING.exists() else 0
    done_count = len(list(DONE.iterdir())) if DONE.exists() else 0
    results["queue"] = {"pending": pending_count, "done": done_count}
    return {"status": "ok", **results}


@executor("run_tests")
def _exec_run_tests(**kw: Any) -> dict:
    import subprocess
    test_dir = kw.get("test_dir", "packages/swarm")
    try:
        r = subprocess.run(
            ["python", "-m", "pytest", test_dir, "-x", "--tb=short", "-q"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=120,
        )
        return {"status": "ok" if r.returncode == 0 else "failed",
                "returncode": r.returncode, "output": r.stdout[-500:] if r.stdout else "",
                "errors": r.stderr[-500:] if r.stderr else ""}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@executor("git_status")
def _exec_git_status(**_kw: Any) -> dict:
    import subprocess
    try:
        r = subprocess.run(["git", "status", "--short"], capture_output=True,
                           text=True, cwd=str(REPO_ROOT), timeout=5)
        dirty = [l.strip() for l in r.stdout.strip().split("\n") if l.strip()]
        r2 = subprocess.run(["git", "log", "--oneline", "-5"], capture_output=True,
                            text=True, cwd=str(REPO_ROOT), timeout=5)
        return {"status": "ok", "dirty_files": len(dirty), "files": dirty[:10],
                "recent_commits": r2.stdout.strip().split("\n")[:5]}
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def process_execute_task(task_path: Path, meta: dict, body: str) -> None:
    """Execute a predefined safe operation with execution_state tracking."""
    task_id = task_path.stem
    executor_name = meta.get("executor", "").strip()
    tracker = AgentExecutionTracker(task_id=task_id, task_title=meta.get("title", task_id))

    if executor_name not in SAFE_EXECUTORS:
        log_event({"event": "execute_rejected", "task_id": task_id,
                    "reason": f"unknown executor: {executor_name}"})
        target = FAILED / task_id
        target.mkdir(parents=True, exist_ok=True)
        shutil.move(str(task_path), str(target / task_path.name))
        (target / "result.json").write_text(json.dumps(
            {"error": f"unknown executor: {executor_name}",
             "execution_state": tracker.to_dict()}, indent=2), encoding="utf-8")
        return

    log_event({"event": "execute_start", "task_id": task_id, "executor": executor_name})
    params: dict[str, str] = {}
    for line in body.strip().splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            params[k.strip()] = v.strip()

    tracker.start()
    while not tracker.is_terminal:
        try:
            result = SAFE_EXECUTORS[executor_name](**params)
            tracker.succeed(result)
        except Exception as e:
            strategy = tracker.handle_failure(e)
            if strategy == "retry":
                tracker.apply_recovery(strategy)
                tracker.start()
                continue
            break

    result = tracker.result if tracker.succeeded else {"status": "failed", "errors": tracker.errors}
    target = (DONE if tracker.succeeded else FAILED) / task_id
    target.mkdir(parents=True, exist_ok=True)
    shutil.move(str(task_path), str(target / task_path.name))
    (target / "result.json").write_text(
        json.dumps({"task_id": task_id, "executor": executor_name,
                    "execution_state": tracker.to_dict(), **(result or {})},
                   indent=2, ensure_ascii=False), encoding="utf-8")
    log_event({"event": "execute_done", "task_id": task_id, "executor": executor_name,
               "state": tracker.state.value, "attempts": tracker.attempt})
    print(f"[{datetime.now().strftime('%H:%M:%S')}] EXEC: {task_id} -> {executor_name} -> {tracker.summary()}", flush=True)


MAX_SELF_TASKS_PER_CYCLE = int(os.getenv("ATLAS_MAX_SELF_TASKS", "5"))
_self_tasks_this_cycle = 0


def create_self_task(task_id: str, task_type: str, title: str, body: str,
                     executor: str | None = None) -> Path | None:
    """Daemon creates its own pending task. Rate-limited to MAX_SELF_TASKS_PER_CYCLE."""
    global _self_tasks_this_cycle
    if _self_tasks_this_cycle >= MAX_SELF_TASKS_PER_CYCLE:
        log_event({"event": "self_task_throttled", "task_id": task_id,
                    "reason": f"cap {MAX_SELF_TASKS_PER_CYCLE}/cycle reached"})
        return None
    dest = PENDING / f"{task_id}.md"
    if dest.exists():
        return None
    done_dir = DONE / task_id
    if done_dir.exists():
        return None
    in_progress_dir = IN_PROGRESS / task_id
    if in_progress_dir.exists():
        return None
    meta_lines = [f"type: {task_type}", f"title: {title}"]
    if executor:
        meta_lines.append(f"executor: {executor}")
    content = f"---\n" + "\n".join(meta_lines) + f"\n---\n{body}\n"
    dest.write_text(content, encoding="utf-8")
    _self_tasks_this_cycle += 1
    log_event({"event": "self_task_created", "task_id": task_id,
               "cycle_count": _self_tasks_this_cycle})
    return dest


SELF_CHECK_INTERVAL = int(os.getenv("ATLAS_SELF_CHECK_INTERVAL", str(10 * 60)))


def _git_last_commit_ts() -> float:
    """Get timestamp of last git commit in REPO_ROOT. Returns 0 on failure."""
    import subprocess
    try:
        r = subprocess.run(
            ["git", "log", "-1", "--format=%ct"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=5,
        )
        return float(r.stdout.strip()) if r.stdout.strip() else 0.0
    except Exception:
        return 0.0


async def run_self_checks() -> None:
    """Daemon inspects its own health and creates tasks for problems found.

    Anti-storm: capped at MAX_SELF_TASKS_PER_CYCLE per invocation.
    Code-index freshness: compared against git commit time, not just file mtime.
    """
    global _self_tasks_this_cycle
    _self_tasks_this_cycle = 0
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    ci = REPO_ROOT / "memory" / "swarm" / "code-index.json"
    index_stale = False
    if not ci.exists():
        index_stale = True
    else:
        ci_mtime = ci.stat().st_mtime
        last_commit_ts = _git_last_commit_ts()
        if last_commit_ts > 0 and ci_mtime < last_commit_ts - 900:
            index_stale = True
        elif (datetime.now(timezone.utc).timestamp() - ci_mtime) > CODE_INDEX_REFRESH_SECONDS:
            index_stale = True
    if index_stale:
        create_self_task(
            f"{today}-auto-reindex", "execute", "Auto-rebuild stale code-index",
            "", executor="rebuild_code_index")

    pw = REPO_ROOT / "memory" / "swarm" / "perspective_weights.json"
    if pw.exists():
        data = json.loads(pw.read_text(encoding="utf-8"))
        stale = [k for k, v in data.items()
                 if v.get("spawn_count", 0) > 0
                 and v.get("last_updated", "") < (datetime.now(timezone.utc).replace(
                     hour=0, minute=0, second=0).isoformat())]
        if len(stale) > 10:
            create_self_task(
                f"{today}-auto-health", "execute",
                "System health check -- stale weights",
                "", executor="local_health")

    # Scan PRE-LAUNCH-BLOCKERS-STATUS.md for unfinished P0 items
    blockers_doc = REPO_ROOT / "docs" / "PRE-LAUNCH-BLOCKERS-STATUS.md"
    if blockers_doc.exists():
        import re
        blockers_text = blockers_doc.read_text(encoding="utf-8")
        unbuilt = re.findall(r"###\s+(\d+\S*)\.\s+(.+?)\s+(🟥|ready to build)", blockers_text, re.IGNORECASE)
        for num, title, _ in unbuilt[:2]:
            create_self_task(
                f"{today}-blocker-{num.strip('.')}", "audit",
                f"Pre-launch blocker #{num}: {title.strip()[:60]}",
                f"PRE-LAUNCH-BLOCKERS-STATUS.md says this is NOT BUILT.\n"
                f"Blocker #{num}: {title.strip()}\n\n"
                f"1. Is this ACTUALLY not built? Check the codebase for existing implementation.\n"
                f"2. If not built: what exact code needs to be written? File paths, functions, estimated lines.\n"
                f"3. If already built: update the blockers doc to mark it done with evidence.\n\n"
                f"READ THE ACTUAL CODE. Do not guess from memory.",
            )

    pending_count = len(list(PENDING.glob("*.md"))) if PENDING.exists() else 0
    in_progress_count = len(list(IN_PROGRESS.iterdir())) if IN_PROGRESS.exists() else 0

    if pending_count == 0 and in_progress_count == 0:
        # Proactive exploration — pick a random important file to deep-read
        import random
        explore_targets = [
            ("apps/api/app/routers/assessment.py", "Assessment engine — core user flow"),
            ("apps/api/app/routers/aura.py", "AURA scoring — badge system"),
            ("apps/api/app/routers/skills.py", "Skills engine — v0Laura core"),
            ("apps/api/app/routers/auth.py", "Authentication — user security"),
            ("apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx", "Dashboard — first user screen"),
            ("apps/api/app/services/ecosystem_events.py", "Ecosystem bridge — cross-product events"),
            ("apps/api/app/routers/organizations.py", "Org admin — B2B flow"),
            ("apps/api/app/routers/grievance.py", "Grievance — compliance flow"),
        ]
        target = random.choice(explore_targets)
        create_self_task(
            f"{today}-explore-{target[0].split('/')[-1].replace('.','_')}", "explore",
            f"Proactive deep-read: {target[1]}",
            f"READ this file thoroughly: {target[0]}\n\n"
            f"Report:\n"
            f"1. What does this file actually do? (not what you assume — what the CODE does)\n"
            f"2. Any bugs, security issues, or Constitution violations?\n"
            f"3. Any dead code or unused imports?\n"
            f"4. Quality: would this pass code review?\n"
            f"5. What would YOU improve if you could?\n\n"
            f"The file content is auto-injected in your context. READ IT.",
        )

        create_self_task(
            f"{today}-auto-audit", "audit", "Daily ecosystem self-audit",
            "Read docs/PRE-LAUNCH-BLOCKERS-STATUS.md FIRST.\n"
            "Then audit each P0 item against actual code.\n"
            "For each: DONE (with file+line evidence) or GAP (with what to build).\n"
            "Do NOT say READY unless every P0 item is verified DONE.",
            executor=None)

    log_event({"event": "self_check_complete", "pending": pending_count,
               "tasks_created": _self_tasks_this_cycle})


async def process_task(task_path: Path) -> None:
    """Process one task file: read, dispatch to swarm, aggregate, archive."""
    task_id = task_path.stem

    text = task_path.read_text(encoding="utf-8")
    meta, body = parse_task_frontmatter(text)

    if meta.get("type") == "execute":
        await process_execute_task(task_path, meta, body)
        return

    log_event({"event": "task_start", "task_id": task_id})

    # Move to in-progress
    work_dir = IN_PROGRESS / task_id
    work_dir.mkdir(parents=True, exist_ok=True)
    moved_task = work_dir / task_path.name
    shutil.move(str(task_path), str(moved_task))

    # Filter perspectives
    allow = meta.get("perspectives", "all")
    if allow == "all":
        chosen = PERSPECTIVES
    else:
        wanted = [n.strip() for n in allow.split(",")]
        chosen = [p for p in PERSPECTIVES if p["name"] in wanted]

    atlas_ctx = load_atlas_context()
    prompts = {p["name"]: build_prompt(p, atlas_ctx, meta, body) for p in chosen}

    # Fire all in parallel
    results = await asyncio.gather(
        *(call_provider_chain(p, prompts[p["name"]]) for p in chosen),
        return_exceptions=True,
    )

    # Per-perspective files
    votes_dir = work_dir / "perspectives"
    votes_dir.mkdir(exist_ok=True)
    parsed_results = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            parsed_results.append({"error": str(r)})
            continue
        parsed = parse_json_safe(r.get("raw", "")) or {}
        # Authoritative perspective name comes from dispatch, not LLM response.
        # qwen3:8b sometimes self-renames to generic labels like "product".
        dispatched_name = chosen[i]["name"] if i < len(chosen) else r.get("perspective", "unknown")
        merged = {**r, **parsed, "perspective": dispatched_name}
        if parsed.get("perspective") and parsed["perspective"] != dispatched_name:
            merged["perspective_name_drift"] = parsed["perspective"]
        parsed_results.append(merged)
        fname = dispatched_name.replace(" ", "_") + ".json"
        (votes_dir / fname).write_text(
            json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    # Aggregate
    summary = {
        "task_id": task_id,
        "task_type": meta.get("type", "audit"),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "perspectives_dispatched": len(chosen),
        "perspectives_responded": sum(1 for r in parsed_results if r.get("provider")),
        "perspectives_failed": sum(1 for r in parsed_results if not r.get("provider")),
        "providers_used": {r.get("provider"): sum(1 for x in parsed_results if x.get("provider") == r.get("provider")) for r in parsed_results if r.get("provider")},
        "whistleblower_flags": [
            {"perspective": r.get("perspective"), "flag": r.get("whistleblower_flag")}
            for r in parsed_results
            if r.get("whistleblower_flag")
        ],
        "perspectives": parsed_results,
    }

    # Move to done or failed
    if summary["perspectives_responded"] == 0:
        target = FAILED / task_id
    else:
        target = DONE / task_id
    target.mkdir(parents=True, exist_ok=True)

    (target / "result.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    if (votes_dir).exists():
        shutil.move(str(votes_dir), str(target / "perspectives"))
    if moved_task.exists():
        shutil.move(str(moved_task), str(target / moved_task.name))
    if work_dir.exists() and not any(work_dir.iterdir()):
        work_dir.rmdir()
    elif work_dir.exists():
        shutil.rmtree(work_dir, ignore_errors=True)

    # ── Learning: update perspective weights from severity scores ──────────
    registry = PerspectiveRegistry(REPO_ROOT)
    SEVERITY_TO_SCORE = {"CRITICAL": 5, "HIGH": 4, "high": 4, "BLOCK": 5,
                         "medium": 3, "MEDIUM": 3, "warn": 2, "WARN": 2,
                         "low": 1, "LOW": 1, "pass": 3, "OK": 3, "fail": 5}
    for r in parsed_results:
        name = r.get("perspective", "")
        if not name or not r.get("provider"):
            continue
        findings = []
        raw = r.get("raw", "")
        if isinstance(raw, str):
            try:
                raw = json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
            except Exception:
                raw = {}
        if isinstance(raw, dict):
            findings = raw.get("findings", [])
        if findings and isinstance(findings, list):
            max_sev = max(
                (SEVERITY_TO_SCORE.get(f.get("severity", ""), 2) for f in findings if isinstance(f, dict)),
                default=2,
            )
            registry.update(name, max_sev)
        else:
            registry.update(name, None)
    log_event({"event": "weights_updated", "task_id": task_id})

    log_event({
        "event": "task_done" if target.parent == DONE else "task_failed",
        "task_id": task_id,
        "summary": {k: v for k, v in summary.items() if k != "perspectives"},
    })
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {target.parent.name.upper()}: {task_id} -- {summary['perspectives_responded']}/{summary['perspectives_dispatched']} responded")

    # Telegram report to CEO — one short message per completed task
    await _telegram_report(task_id, meta, summary)


async def _telegram_report(task_id: str, meta: dict, summary: dict) -> None:
    """Send concise task completion report to CEO via Telegram."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CEO_CHAT_ID", "")
    if not token or not chat_id:
        return

    responded = summary.get("perspectives_responded", 0)
    dispatched = summary.get("perspectives_dispatched", 0)
    task_type = meta.get("type", "?")
    title = meta.get("title", task_id)[:80]

    flags = [f for f in summary.get("whistleblower_flags", [])
             if f.get("flag") and f["flag"] != "null"]

    # Count critical findings
    crits = 0
    verdicts: dict[str, int] = {}
    for p in summary.get("perspectives", []):
        raw = p.get("raw", "")
        if isinstance(raw, str):
            try:
                raw = json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
            except Exception:
                continue
        v = str(raw.get("overall_verdict", raw.get("vote", "?"))).lower()
        verdicts[v] = verdicts.get(v, 0) + 1
        for f in raw.get("findings", []):
            if isinstance(f, dict) and str(f.get("severity", "")).lower() in ("critical", "p0", "block"):
                crits += 1

    verdict_str = ", ".join(f"{v}={c}" for v, c in sorted(verdicts.items(), key=lambda x: -x[1])[:3])

    msg = f"Swarm [{task_type}]: {title}\n"
    msg += f"{responded}/{dispatched} responded | {verdict_str}\n"
    if crits:
        msg += f"CRITICAL: {crits}\n"
    if flags:
        msg += f"WHISTLEBLOWER: {len(flags)}\n"
        for fl in flags[:2]:
            msg += f"  {fl['perspective']}: {str(fl['flag'])[:80]}\n"

    import urllib.request
    import urllib.parse
    try:
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": msg,
            "disable_web_page_preview": "true",
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=data, method="POST",
        )
        with urllib.request.urlopen(req, timeout=10):
            pass
        log_event({"event": "telegram_report_sent", "task_id": task_id})
    except Exception as e:
        log_event({"event": "telegram_report_failed", "task_id": task_id, "error": str(e)[:100]})

    # PostHog: track each perspective call as LLM analytics event
    for p in summary.get("perspectives", []):
        _track_llm_call(
            perspective=p.get("perspective", "?"),
            provider=p.get("provider", "?"),
            model=p.get("model", "?"),
            duration_ms=0,  # not tracked per-call yet
            task_id=task_id,
            success=bool(p.get("provider")),
        )


def handle_signal(signum, frame):
    global shutdown_requested
    shutdown_requested = True
    print("\n[daemon] shutdown requested, finishing current task ...", flush=True)


CODE_INDEX_REFRESH_SECONDS = int(os.getenv("ATLAS_CODE_INDEX_REFRESH", str(6 * 3600)))


def maybe_rebuild_code_index(force: bool = False) -> None:
    """Rebuild code-index.json if stale (>CODE_INDEX_REFRESH_SECONDS) or forced."""
    try:
        if force or not INDEX_FILE.exists():
            idx = build_index(REPO_ROOT)
            log_event({"event": "code_index_rebuilt", "total_files": idx["total_files"]})
            print(f"[daemon] code-index rebuilt: {idx['total_files']} files", flush=True)
            return
        age = datetime.now(timezone.utc).timestamp() - INDEX_FILE.stat().st_mtime
        if age > CODE_INDEX_REFRESH_SECONDS:
            idx = build_index(REPO_ROOT)
            log_event({"event": "code_index_rebuilt", "total_files": idx["total_files"], "stale_seconds": int(age)})
            print(f"[daemon] code-index rebuilt (stale {int(age)}s): {idx['total_files']} files", flush=True)
    except Exception as e:
        log_event({"event": "code_index_error", "error": str(e)})


async def main():
    global _ollama_semaphore
    _ollama_semaphore = asyncio.Semaphore(OLLAMA_CONCURRENCY)
    setup_dirs()
    maybe_rebuild_code_index(force=True)
    log_event({"event": "daemon_start", "poll_interval": POLL_INTERVAL_SECONDS, "ollama_concurrency": OLLAMA_CONCURRENCY})
    print(f"[daemon] started. polling {PENDING} every {POLL_INTERVAL_SECONDS}s. Ollama concurrency={OLLAMA_CONCURRENCY}. Ctrl+C to stop.", flush=True)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

    _last_index_check = datetime.now(timezone.utc).timestamp()
    _last_self_check = 0.0

    while not shutdown_requested:
        try:
            setup_dirs()
            now_ts = datetime.now(timezone.utc).timestamp()
            if now_ts - _last_index_check > CODE_INDEX_REFRESH_SECONDS:
                maybe_rebuild_code_index()
                _last_index_check = now_ts
            if now_ts - _last_self_check > SELF_CHECK_INTERVAL:
                await run_self_checks()
                _last_self_check = now_ts
            tasks = sorted(PENDING.glob("*.md"))
            if tasks:
                async def _wrap(t):
                    async with semaphore:
                        await process_task(t)
                await asyncio.gather(*(_wrap(t) for t in tasks))
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
        except Exception as e:
            log_event({"event": "daemon_error", "error": str(e)})
            print(f"[daemon] ERROR: {e}", flush=True)
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    log_event({"event": "daemon_stop"})
    print("[daemon] stopped cleanly.", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
