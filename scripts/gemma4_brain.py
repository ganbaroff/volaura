#!/usr/bin/env python3
"""gemma4_brain.py — Gemma4 as the permanent swarm brain.

CEO: "надо продумать как делать так чтобы не терялся весь проект.
в каждом моменте объяснять что происходит."

Gemma4 runs on CEO's RTX 5060. Never sleeps while the machine is on.
Reads ALL project MD files → understands the full project → creates
tasks for the 17-agent swarm daemon → monitors results → creates
follow-up tasks.

Flow:
1. Boot: read all priority MD files into context
2. Analyze: what needs to be done based on project state
3. Dispatch: create task files in work-queue/pending/
4. Monitor: watch work-queue/done/ for completed tasks
5. Learn: read results, update strategy, create follow-up tasks
6. Loop forever (sleep between cycles)

Usage:
  python scripts/gemma4_brain.py           # foreground
  pythonw scripts/gemma4_brain.py          # background (no console)
"""

import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Patch 2 (2026-05-09) — Orchestrator-Workers planner contract
ROUTING_CATEGORIES: set[str] = {"audit", "refactor", "feature", "bug"}
PRIORITIES: set[str] = {"P0", "P1", "P2"}
CONFIDENCE_LEVELS: set[str] = {"high", "medium", "low"}
MIN_TASKS_PER_CYCLE: int = 3
MAX_TASKS_PER_CYCLE: int = 5

REPO_ROOT = Path(__file__).resolve().parent.parent
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
GEMMA4_MODEL = "gemma4"

QUEUE = REPO_ROOT / "memory" / "atlas" / "work-queue"
PENDING = QUEUE / "pending"
DONE = QUEUE / "done"
BRAIN_LOG = QUEUE / "brain.log.jsonl"

# How often the brain thinks (seconds)
THINK_INTERVAL = 300  # 5 minutes
# How often to re-read project state
FULL_REREAD_INTERVAL = 3600  # 1 hour

# Compact canonical input — architecture mandate: NO giant text dumps
# Only these 7 sources. Target < 15K chars total.
PRIORITY_FILES = [
    "memory/atlas/semantic/product-truth.md",       # what VOLAURA is
    "memory/atlas/semantic/swarm-state.md",          # swarm architecture
    "memory/atlas/semantic/swarm-commands.md",       # what to do next
    "memory/atlas/semantic/false-positives.md",      # don't repeat these
    "memory/atlas/semantic/architecture-mandate.md", # how to work
    "docs/PRE-LAUNCH-BLOCKERS-STATUS.md",            # current blockers
    ".claude/breadcrumb.md",                         # session state
]

# No secondary patterns — architecture mandate forbids giant dumps
SECONDARY_PATTERNS = []


def log_event(event: dict) -> None:
    event["ts"] = datetime.now(timezone.utc).isoformat()
    BRAIN_LOG.parent.mkdir(parents=True, exist_ok=True)
    with BRAIN_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def read_project_context(full: bool = False) -> str:
    """Read priority MD files into a single context string."""
    parts = []
    total_chars = 0
    max_chars = 15_000  # compact canonical input per architecture mandate

    # Priority files first
    for rel in PRIORITY_FILES:
        fp = REPO_ROOT / rel
        if not fp.exists():
            continue
        text = fp.read_text(encoding="utf-8", errors="replace")
        if total_chars + len(text) > max_chars:
            text = text[:max_chars - total_chars]
            parts.append(f"=== {rel} (TRUNCATED) ===\n{text}")
            total_chars = max_chars
            break
        parts.append(f"=== {rel} ===\n{text}")
        total_chars += len(text)

    # Secondary files on full reread
    if full and total_chars < max_chars:
        for pattern in SECONDARY_PATTERNS:
            for fp in sorted(REPO_ROOT.glob(pattern)):
                if total_chars >= max_chars:
                    break
                rel = str(fp.relative_to(REPO_ROOT))
                if rel in PRIORITY_FILES:
                    continue
                try:
                    text = fp.read_text(encoding="utf-8", errors="replace")
                    if total_chars + len(text) > max_chars:
                        text = text[:max_chars - total_chars]
                        parts.append(f"=== {rel} (TRUNCATED) ===\n{text}")
                        total_chars = max_chars
                        break
                    parts.append(f"=== {rel} ===\n{text}")
                    total_chars += len(text)
                except Exception:
                    continue

    return "\n\n".join(parts)


def get_pending_count() -> int:
    return len(list(PENDING.glob("*.md"))) if PENDING.exists() else 0


def get_recent_done(n: int = 5) -> list[dict]:
    """Read last N completed task results."""
    if not DONE.exists():
        return []
    results = []
    for task_dir in sorted(DONE.iterdir(), reverse=True)[:n]:
        result_file = task_dir / "result.json"
        if result_file.exists():
            try:
                data = json.loads(result_file.read_text(encoding="utf-8"))
                results.append({
                    "task_id": data.get("task_id", task_dir.name),
                    "type": data.get("task_type", "?"),
                    "responded": data.get("perspectives_responded", 0),
                    "dispatched": data.get("perspectives_dispatched", 0),
                    "whistleblowers": len(data.get("whistleblower_flags", [])),
                })
            except Exception:
                pass
    return results


_DEDUP_STOP_WORDS: set[str] = {
    # Articles / particles
    "the", "a", "an", "in", "on", "at", "to", "of", "for", "with", "from",
    "via", "by", "and", "or", "as", "into", "across", "per",
    # Weak verbs Brain LLM tends to alternate between cycles
    "fix", "audit", "verify", "check", "review", "ensure", "restore",
    "calibrate", "implement", "address", "handle", "resolve", "enforce",
    "validate", "test", "perform", "do", "make", "ensure",
    # Soft modifiers and container nouns brain alternates between
    "compliance", "violation", "issue", "flow", "logic", "rules", "data",
    "real", "live", "current", "system", "systemic", "core", "main",
    "section", "checklist", "blockers", "blocker", "task", "tasks",
    # Platform/UI noise — same task gets phrased "in web" / "in web UI" /
    # "in VOLAURA web" by the brain LLM across cycles. Treat as noise.
    "ui", "ux", "web", "frontend", "backend", "volaura", "platform",
    "app", "application", "component", "components", "page", "pages",
    "module", "modules",
    # File-extension token noise after punctuation strip
    "md", "tsx", "ts", "js", "json", "yaml", "yml", "py", "html", "css",
    "toml", "config", "configuration",
}


def _normalize_title_key(title: str) -> str:
    """Deterministic dedup key for a brain task title.

    Lowercase, strip punctuation, drop stop-words and weak verbs, sort the
    remaining content tokens, and join with single space. Two titles that
    differ only by article/punctuation/weak-verb wording collapse to the
    same key. CEO directive 2026-05-09 (Codex relay): tupoy slой first,
    semantic similarity layered later only if dupes still leak.
    """
    if not isinstance(title, str):
        return ""
    cleaned = re.sub(r"[^\w\s]", " ", title.lower())
    tokens = [
        t.strip()
        for t in cleaned.split()
        if t.strip() and t.strip() not in _DEDUP_STOP_WORDS
    ]
    return " ".join(sorted(tokens))


_DEDUP_DONE_LOOKBACK: int = 20  # last N done dirs to scan


def _existing_task_keys() -> set[str]:
    """Collect normalized title keys from pending, in-progress, and recent done.

    Brain calls this before each create_task to decide whether the proposed
    task is a near-duplicate of work already on the queue or recently
    completed. Cheap directory scan, runs once per cycle.
    """
    keys: set[str] = set()

    def _harvest_md_dir(d: Path) -> None:
        if not d.exists():
            return
        for p in d.glob("*.md"):
            try:
                head = p.read_text(encoding="utf-8")[:500]
            except Exception:
                continue
            for line in head.splitlines():
                if line.lower().startswith("title:"):
                    title = line.split(":", 1)[1].strip()
                    keys.add(_normalize_title_key(title))
                    break

    _harvest_md_dir(PENDING)
    in_progress = QUEUE / "in-progress"
    _harvest_md_dir(in_progress)

    if DONE.exists():
        for task_dir in sorted(DONE.iterdir(), reverse=True)[:_DEDUP_DONE_LOOKBACK]:
            # Done directories may store the original task either as
            # <task_id>.md inside the dir, or under task.json.
            md = task_dir / f"{task_dir.name}.md"
            if md.exists():
                try:
                    head = md.read_text(encoding="utf-8")[:500]
                    for line in head.splitlines():
                        if line.lower().startswith("title:"):
                            title = line.split(":", 1)[1].strip()
                            keys.add(_normalize_title_key(title))
                            break
                    continue
                except Exception:
                    pass
            tj = task_dir / "task.json"
            if tj.exists():
                try:
                    data = json.loads(tj.read_text(encoding="utf-8"))
                    title = str(data.get("title", "")).strip()
                    if title:
                        keys.add(_normalize_title_key(title))
                except Exception:
                    pass

    keys.discard("")
    return keys


def create_task(
    task_id: str,
    task_type: str,
    title: str,
    body: str,
    seen_keys: set[str] | None = None,
) -> bool:
    """Drop a task file for the daemon to pick up.

    If ``seen_keys`` is provided, the task title's normalized key is checked
    against that set BEFORE writing. A match → skip the task and emit
    ``brain_task_dedup_skipped`` event. The caller is expected to update
    ``seen_keys`` after a successful create so subsequent calls in the same
    cycle don't emit duplicates either.

    Returns True if the task was newly created, False if skipped (either
    file already exists or normalized title already in ``seen_keys``).
    """
    PENDING.mkdir(parents=True, exist_ok=True)
    task_file = PENDING / f"{task_id}.md"
    if task_file.exists():
        return False  # exact-id dedup (already on queue)

    if seen_keys is not None:
        norm = _normalize_title_key(title)
        if norm and norm in seen_keys:
            log_event({
                "event": "brain_task_dedup_skipped",
                "task_id": task_id,
                "title": title,
                "normalized_key": norm,
                "reason": "title key matches existing pending / in-progress / recent done task",
            })
            return False
        if norm:
            seen_keys.add(norm)

    content = f"""---
type: {task_type}
title: {title}
perspectives: all
---
{body}
"""
    task_file.write_text(content, encoding="utf-8")
    log_event({"event": "brain_created_task", "task_id": task_id, "title": title})
    return True


def _try_groq(prompt: str, max_tokens: int) -> str | None:
    """Provider 1 (default first per ADR-013). Free tier, llama-3.3-70b."""
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        return None
    try:
        import urllib.request
        payload = json.dumps({
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4,
            "max_tokens": max_tokens,
        }).encode()
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {key}",
                     "User-Agent": "VolauraBrain/1.0"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
            content = data["choices"][0]["message"]["content"]
            log_event({"event": "brain_llm_call", "provider": "groq", "model": "llama-3.3-70b"})
            return content
    except Exception as e:
        log_event({"event": "brain_llm_failed", "provider": "groq", "error": str(e)[:150]})
        return None


def _try_gemini(prompt: str, max_tokens: int) -> str | None:
    """Provider 2 — Google credits backed (Vertex/Gemini API). Default fallback after Groq."""
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        return None
    try:
        import urllib.request
        payload = json.dumps({
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": max_tokens},
        }).encode()
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-2.0-flash:generateContent?key=" + key
        )
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json",
                     "User-Agent": "VolauraBrain/1.0"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("no candidates returned")
            parts = candidates[0].get("content", {}).get("parts", [])
            content = "".join(p.get("text", "") for p in parts)
            if content:
                log_event({"event": "brain_llm_call", "provider": "gemini", "model": "gemini-2.0-flash"})
                return content
            raise ValueError("empty content from gemini")
    except Exception as e:
        log_event({"event": "brain_llm_failed", "provider": "gemini", "error": str(e)[:150]})
        return None


def _try_nvidia(prompt: str, max_tokens: int) -> str | None:
    """Provider 3 — NVIDIA Inception credits. Free tier through NIM."""
    key = os.getenv("NVIDIA_API_KEY", "")
    if not key:
        return None
    try:
        import urllib.request
        payload = json.dumps({
            "model": "meta/llama-3.3-70b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4,
            "max_tokens": max_tokens,
        }).encode()
        req = urllib.request.Request(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {key}",
                     "User-Agent": "VolauraBrain/1.0"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
            content = data["choices"][0]["message"]["content"]
            log_event({"event": "brain_llm_call", "provider": "nvidia", "model": "meta-llama-3.3-70b"})
            return content
    except Exception as e:
        log_event({"event": "brain_llm_failed", "provider": "nvidia", "error": str(e)[:150]})
        return None


def _try_ollama(prompt: str, max_tokens: int) -> str | None:
    """Provider 4 — Ollama local (Gemma4, CEO's RTX 5060 if running locally)."""
    try:
        import urllib.request
        payload = json.dumps({
            "model": GEMMA4_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.5, "num_predict": max_tokens},
        }).encode()
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=600) as resp:
            data = json.loads(resp.read())
            content = data.get("response", "")
            if content:
                log_event({"event": "brain_llm_call", "provider": "ollama", "model": GEMMA4_MODEL})
                return content
    except Exception:
        pass
    return None


def call_brain_llm(prompt: str, max_tokens: int = 4000) -> str:
    """Call brain LLM. Provider precedence per AGENTS.md §35 + CLAUDE.md + ADR-013:

        NVIDIA NIM -> Ollama (local) -> Gemini Flash -> Groq

    Cerebras was FULLY REMOVED from this chain after the 2026-05-09 $7.25/$10 burn
    (ADR-013 §a; lessons.md Class 38/42). It is never called — not even with
    ATLAS_ENABLE_CEREBRAS=true — and the `_try_cerebras` function was deleted so a
    future refactor cannot re-promote it without re-adding code the provider-chain
    tests (tests/test_gemma4_brain_provider_chain.py) reject.

    Returns first non-empty content from the chain, or empty string if every
    provider failed.
    """
    for tryer in (_try_nvidia, _try_ollama, _try_gemini, _try_groq):
        content = tryer(prompt, max_tokens)
        if content:
            return content
    log_event({"event": "brain_all_providers_failed"})
    return ""


def parse_brain_json(raw: str) -> dict | None:
    """Patch 2 (2026-05-09): JSON-first parser with three repair stages.

    Strategy:
      1. Strict ``json.loads`` on the trimmed raw string.
      2. If the model wrapped output in ```json ... ``` fences, extract.
      3. Last resort: take substring from first ``{`` to last ``}``.

    Returns the parsed dict, or None if all stages fail. None signals the
    caller to fall back to ``_legacy_parse`` for backward compatibility.
    """
    if not isinstance(raw, str):
        return None
    raw = raw.strip()
    if not raw:
        return None

    try:
        result = json.loads(raw)
        return result if isinstance(result, dict) else None
    except Exception:
        pass

    if "```" in raw:
        m = re.search(r"```(?:json)?\s*(.+?)\s*```", raw, re.DOTALL)
        if m:
            try:
                result = json.loads(m.group(1).strip())
                return result if isinstance(result, dict) else None
            except Exception:
                pass

    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        try:
            result = json.loads(raw[start:end + 1])
            return result if isinstance(result, dict) else None
        except Exception:
            pass

    return None


def validate_brain_task(task: Any) -> tuple[bool, str]:
    """Validate one structured brain task. Return (ok, reason_if_rejected).

    Patch 2 (2026-05-09) contract:
    - title (non-empty)
    - type (one of ROUTING_CATEGORIES)
    - rationale (non-empty)
    - confidence (one of CONFIDENCE_LEVELS, default 'high')
    - expected_evidence_path + (expected_evidence_line OR
      expected_evidence_anchor) — REQUIRED unless confidence='low'.
    - low_confidence_reason — REQUIRED when confidence='low'.

    No silent empty-task success path: a task without an evidence anchor
    is rejected unless explicitly marked low-confidence with reason.
    """
    if not isinstance(task, dict):
        return False, "task is not a dict"

    title = str(task.get("title") or "").strip()
    if not title:
        return False, "missing title"

    ttype = str(task.get("type") or "").strip().lower()
    if ttype not in ROUTING_CATEGORIES:
        return False, f"invalid type {ttype!r}; expected one of {sorted(ROUTING_CATEGORIES)}"

    rationale = str(task.get("rationale") or "").strip()
    if not rationale:
        return False, "missing rationale"

    confidence_raw = task.get("confidence", "high")
    confidence = str(confidence_raw).strip().lower() if confidence_raw is not None else "high"
    if confidence not in CONFIDENCE_LEVELS:
        return False, f"invalid confidence {confidence!r}"

    evidence_path = str(task.get("expected_evidence_path") or "").strip()
    evidence_line = task.get("expected_evidence_line")
    evidence_anchor = str(task.get("expected_evidence_anchor") or "").strip()
    has_anchor = bool(evidence_path) and (evidence_line is not None or bool(evidence_anchor))

    if confidence == "low":
        low_reason = str(task.get("low_confidence_reason") or "").strip()
        if not low_reason:
            return False, "confidence='low' requires non-empty low_confidence_reason"
    elif not has_anchor:
        return False, "no evidence anchor (need expected_evidence_path + expected_evidence_line or expected_evidence_anchor) and confidence is not 'low'"

    return True, ""


def build_task_body(task: dict, parent_analysis: str) -> str:
    """Render a structured task into the markdown body the daemon consumes.

    Frontmatter is added by ``create_task``. This function only produces
    the body section so the daemon's existing parser sees a normal
    markdown task.
    """
    title = task["title"]
    ttype = task["type"]
    priority = str(task.get("priority", "P2"))
    confidence = str(task.get("confidence", "high"))
    rationale = task.get("rationale", "(no rationale)")
    evp = str(task.get("expected_evidence_path") or "").strip()
    evl = task.get("expected_evidence_line")
    eva = str(task.get("expected_evidence_anchor") or "").strip()
    low_reason = str(task.get("low_confidence_reason") or "").strip()

    lines: list[str] = [
        f"# {title}",
        "",
        f"**Routing category:** {ttype}",
        f"**Priority:** {priority}",
        f"**Confidence:** {confidence}",
        "",
        "## Rationale",
        rationale,
        "",
        "## Expected evidence anchor",
    ]
    if evp and evl is not None:
        lines.append(f"- `{evp}:{evl}` — daemon Phase C will fetch the bytes here.")
    elif evp and eva:
        lines.append(f"- `{evp}` (anchor: {eva}) — Phase C may not auto-excerpt without a numeric line.")
    elif evp:
        lines.append(f"- `{evp}` — confidence={confidence}, no line anchor.")
    else:
        lines.append("- (no path) — see low_confidence_reason below.")

    if confidence == "low" and low_reason:
        lines.extend(["", "## Low confidence reason", low_reason])

    if parent_analysis:
        lines.extend(["", "## Cycle analysis (orchestrator)", parent_analysis])

    return "\n".join(lines).strip() + "\n"


def _legacy_parse(response: str) -> list[dict]:
    """Backward-compat fallback when JSON parse fails.

    Uses the original ANALYSIS / TASK1_TYPE / TASK1_TITLE / TASK1_BODY
    regex format from the pre-Patch-2 implementation. Returns up to 2
    tasks shaped like the Patch 2 contract minimally (title, type,
    rationale, confidence='low', low_confidence_reason).
    """
    if not isinstance(response, str) or not response:
        return []

    out: list[dict] = []
    for i in [1, 2]:
        type_match = re.search(rf"TASK{i}_TYPE:\s*(\w+)", response)
        title_match = re.search(rf"TASK{i}_TITLE:\s*(.+?)(?=TASK{i}_BODY:|$)", response, re.DOTALL)
        body_match = re.search(rf"TASK{i}_BODY:\s*(.+?)(?=TASK{i+1}_TYPE:|$)", response, re.DOTALL)
        if not (type_match and title_match):
            continue
        ttype = type_match.group(1).strip().lower()
        title = title_match.group(1).strip()[:80]
        body = body_match.group(1).strip()[:500] if body_match else title
        if ttype == "none" or title.lower() == "none":
            continue
        if ttype not in ROUTING_CATEGORIES:
            ttype = "audit"
        out.append({
            "title": title,
            "type": ttype,
            "rationale": body,
            "confidence": "low",
            "low_confidence_reason": "legacy regex parse path — model did not return structured JSON",
            "priority": "P2",
        })
    return out


async def think_cycle(project_context: str) -> None:
    """Patch 2 (2026-05-09) — Orchestrator-Workers cycle.

    Flow:
      1. Snapshot queue + recent done.
      2. Build focused context (same trimming as before).
      3. Prompt the brain LLM for strict JSON with routing_category,
         analysis, and 3-5 tasks each with evidence anchors.
      4. Parse with ``parse_brain_json``; fall back to legacy regex on
         failure for backward compat.
      5. Validate every task with ``validate_brain_task``; reject silently
         dangerous shapes.
      6. Cap to MAX_TASKS_PER_CYCLE; create_task for each survivor.
    """
    pending = get_pending_count()
    recent_done = get_recent_done(5)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    done_summary = ""
    if recent_done:
        done_summary = "Recent completed tasks:\n"
        for d in recent_done:
            done_summary += f"  - {d['task_id']}: {d['type']}, {d['responded']}/{d['dispatched']} responded"
            if d['whistleblowers']:
                done_summary += f", {d['whistleblowers']} whistleblower flags"
            done_summary += "\n"

    # Same trimming as pre-Patch-2 — Gemma4 8B works better with focused input.
    focused_parts: list[str] = []
    for section in project_context.split("=== "):
        if not section.strip():
            continue
        header = section.split("\n")[0]
        if any(k in header for k in [
            "PRE-LAUNCH-BLOCKERS", "product-truth", "swarm-state",
            "breadcrumb", "lessons", "daily-health"
        ]):
            focused_parts.append("=== " + section[:4000])
    focused_context = "\n\n".join(focused_parts)
    if not focused_context:
        focused_context = project_context[:20000]

    prompt = f"""You are the BRAIN of the VOLAURA swarm. Plan {MIN_TASKS_PER_CYCLE}-{MAX_TASKS_PER_CYCLE} tasks for the 17-agent daemon.

KNOWN ISSUES:
1. Foundation Law 2 (Energy Adaptation) MISSING in VOLAURA web — 18 days broken.
2. IRT assessment parameters NOT calibrated on real data.
3. Pre-launch blockers open (see BLOCKERS section).

QUEUE STATE: {pending} pending tasks
{done_summary}

PROJECT STATE:
{focused_context[:30000]}

Reply with strict JSON. Only JSON. No preamble, no fences, no commentary.

Schema:
{{
  "analysis": "1-2 sentences about current state",
  "routing_category": "audit | refactor | feature | bug",
  "tasks": [
    {{
      "title": "specific title under 80 chars",
      "type": "audit | refactor | feature | bug",
      "rationale": "why this task now, what it unblocks",
      "expected_evidence_path": "exact repo path, e.g. apps/api/app/routers/auth.py",
      "expected_evidence_line": 119,
      "priority": "P0 | P1 | P2",
      "confidence": "high | medium | low",
      "low_confidence_reason": "ONLY when confidence='low'; explain why no line anchor"
    }}
  ]
}}

Rules:
- Emit {MIN_TASKS_PER_CYCLE} to {MAX_TASKS_PER_CYCLE} tasks.
- Every task MUST have expected_evidence_path AND expected_evidence_line.
- If a task genuinely cannot have a line anchor, set confidence='low' AND include low_confidence_reason. Do not emit speculative tasks with no anchor and high confidence.
- type must be one of: audit, refactor, feature, bug.
- priority P0 for blockers, P1 for important, P2 for nice-to-have.
"""

    try:
        response = call_brain_llm(prompt, 2400)
    except Exception as e:
        log_event({"event": "brain_think_error", "error": str(e)[:200]})
        return
    if not response or not isinstance(response, str):
        log_event({"event": "brain_think_empty"})
        return

    parsed = parse_brain_json(response)
    used_fallback = False
    if parsed is None:
        log_event({"event": "brain_json_parse_failed", "fallback": "regex_legacy",
                   "response_head": response[:200]})
        legacy_tasks = _legacy_parse(response)
        if not legacy_tasks:
            log_event({"event": "brain_no_tasks", "reason": "json_failed_and_legacy_empty"})
            return
        parsed = {
            "analysis": "(parsed from legacy regex fallback)",
            "routing_category": "audit",
            "tasks": legacy_tasks,
        }
        used_fallback = True

    analysis = str(parsed.get("analysis") or "")[:300] or "no analysis"
    routing_cat = str(parsed.get("routing_category") or "audit").strip().lower()
    raw_tasks = parsed.get("tasks", [])
    if not isinstance(raw_tasks, list):
        log_event({"event": "brain_tasks_not_list", "type": type(raw_tasks).__name__})
        return

    valid_tasks: list[dict] = []
    rejected: list[dict] = []
    for t in raw_tasks:
        ok, reason = validate_brain_task(t)
        if ok:
            valid_tasks.append(t)
        else:
            rejected.append({"title": (t.get("title") if isinstance(t, dict) else str(t))[:80] if isinstance(t, dict) else "?", "reason": reason})

    if not valid_tasks:
        log_event({"event": "brain_no_valid_tasks", "rejected": rejected,
                   "fallback_used": used_fallback})
        return

    valid_tasks = valid_tasks[:MAX_TASKS_PER_CYCLE]

    # Build the dedup key set ONCE per cycle (CEO directive 2026-05-09 via
    # Codex: deterministic dedup first, semantic later only if needed).
    seen_keys = _existing_task_keys()
    pre_existing = len(seen_keys)

    log_event({
        "event": "brain_think",
        "analysis": analysis,
        "routing_category": routing_cat,
        "tasks_planned": len(valid_tasks),
        "rejected_count": len(rejected),
        "fallback_used": used_fallback,
        "dedup_existing_keys": pre_existing,
    })
    print(f"[brain {datetime.now().strftime('%H:%M:%S')}] {analysis}", flush=True)

    skipped_dedup = 0
    for idx, task in enumerate(valid_tasks):
        tid = f"{today}-brain-{idx+1}"
        ttype = task["type"]
        title = task["title"]
        body = build_task_body(task, analysis)
        if create_task(tid, ttype, title, body, seen_keys=seen_keys):
            priority = task.get("priority", "P2")
            print(f"[brain] -> created: {tid} ({ttype}/{priority}): {title}", flush=True)
        else:
            skipped_dedup += 1
            print(f"[brain] -> skipped (dedup or exists): {tid}: {title}", flush=True)

    if skipped_dedup:
        log_event({
            "event": "brain_dedup_summary",
            "tasks_planned": len(valid_tasks),
            "tasks_skipped": skipped_dedup,
            "tasks_created": len(valid_tasks) - skipped_dedup,
        })


async def main():
    print(f"[brain] Gemma4 brain starting. Model: {GEMMA4_MODEL}", flush=True)
    print(f"[brain] Think interval: {THINK_INTERVAL}s, Full reread: {FULL_REREAD_INTERVAL}s", flush=True)

    # Ensure dirs exist
    PENDING.mkdir(parents=True, exist_ok=True)

    # Initial full read
    print("[brain] Reading full project context...", flush=True)
    context = read_project_context(full=True)
    print(f"[brain] Context loaded: {len(context)} chars from project files", flush=True)
    log_event({"event": "brain_start", "context_chars": len(context)})

    last_full_read = time.time()
    cycle = 0

    while True:
        cycle += 1
        now = time.time()

        # Full reread every hour
        if now - last_full_read > FULL_REREAD_INTERVAL:
            print("[brain] Full project reread...", flush=True)
            context = read_project_context(full=True)
            last_full_read = now
        else:
            # Quick reread of priority files only
            context = read_project_context(full=False)

        try:
            await think_cycle(context)
        except Exception as e:
            log_event({"event": "brain_error", "error": str(e)[:200]})
            print(f"[brain] ERROR: {e}", flush=True)

        print(f"[brain] Cycle {cycle} done. Sleeping {THINK_INTERVAL}s...", flush=True)
        await asyncio.sleep(THINK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
