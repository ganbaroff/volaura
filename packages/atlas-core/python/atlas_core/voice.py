"""Atlas voice validator — pure local regex/heuristic.

Given a raw LLM output, returns whether it matches Atlas voice rules.
Mirrors heuristics in .claude/hooks/voice-breach-check.sh but usable
from production code (FastAPI middleware, Next.js API route, swarm
agent self-check). No LLM call. No network. No filesystem.

Callers decide block vs warn — this module only reports.
"""
from __future__ import annotations

import re
from typing import List

from pydantic import BaseModel, ConfigDict


class Breach(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: str
    sample: str
    rule_ref: str


class VoiceCheckResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    passed: bool
    breaches: List[Breach]


# Rule references point at canonical docs so a human can go read why.
_RULE_VOICE_MD = "memory/atlas/voice.md"
_RULE_PRINCIPLES = ".claude/rules/atlas-operating-principles.md"

# Banned openers — any one of these as first non-empty line.
_BANNED_OPENERS = (
    "Готово. Вот что я сделал",
    "Отлично!",
)

# Bold-as-header: lines starting with ** followed by a letter (Latin or Cyrillic).
_BOLD_HEADER_RE = re.compile(r"^\*\*[A-Za-zА-Яа-яЁё]")
# Markdown heading: # .. #### followed by whitespace.
_HEADING_RE = re.compile(r"^#{1,4}\s")
# Bullet line: - or * followed by space and letter or **.
_BULLET_RE = re.compile(r"^\s*[-*]\s+[A-Za-zА-Яа-яЁё\*]")
# Markdown table separator row.
_TABLE_SEP_RE = re.compile(r"^\s*\|[-:\s|]+\|\s*$")
# Option/variant markers — legitimate reason to end on "?" (asking user to choose).
_OPTION_MARKER_RE = re.compile(r"\b(option|variant|вариант|опция)\b", re.IGNORECASE)


def _first_nonempty_line(lines: List[str]) -> str:
    for line in lines:
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _last_nonempty_line(lines: List[str]) -> str:
    for line in reversed(lines):
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def validate_voice(text: str) -> VoiceCheckResult:
    """Validate text against Atlas voice rules. Pure function, no side effects."""
    breaches: List[Breach] = []
    lines = text.split("\n")

    # Rule 1: bold-headers (3+ lines starting with **)
    bold_header_lines = [l for l in lines if _BOLD_HEADER_RE.match(l.strip())]
    if len(bold_header_lines) >= 3:
        breaches.append(
            Breach(
                type="bold-headers-in-chat",
                sample=bold_header_lines[0][:120],
                rule_ref=f"{_RULE_VOICE_MD}#banned-structural-habits",
            )
        )

    # Rule 2: markdown headings
    heading_lines = [l for l in lines if _HEADING_RE.match(l)]
    if heading_lines:
        breaches.append(
            Breach(
                type="markdown-heading",
                sample=heading_lines[0][:120],
                rule_ref=f"{_RULE_VOICE_MD}#banned-structural-habits",
            )
        )

    # Rule 3: bullet-wall (4+ bullets inside 10-line sliding window)
    bullet_indices = [i for i, l in enumerate(lines) if _BULLET_RE.match(l)]
    wall_found = False
    for i in range(len(bullet_indices) - 3):
        if bullet_indices[i + 3] - bullet_indices[i] <= 10:
            wall_found = True
            break
    if wall_found:
        breaches.append(
            Breach(
                type="bullet-wall",
                sample=lines[bullet_indices[0]][:120],
                rule_ref=f"{_RULE_VOICE_MD}#banned-structural-habits",
            )
        )

    # Rule 4: markdown-table (separator row present)
    table_rows = [l for l in lines if _TABLE_SEP_RE.match(l)]
    if table_rows:
        breaches.append(
            Breach(
                type="markdown-table-in-conversation",
                sample=table_rows[0][:120],
                rule_ref=f"{_RULE_VOICE_MD}#banned-structural-habits",
            )
        )

    # Rule 5: trailing-question on reversible (last line <100 chars, ends in ?,
    # no option/variant markers anywhere in the text)
    last = _last_nonempty_line(lines)
    if (
        last
        and last.endswith("?")
        and len(last) < 100
        and not _OPTION_MARKER_RE.search(text)
    ):
        breaches.append(
            Breach(
                type="trailing-question-on-reversible",
                sample=last[:120],
                rule_ref=f"{_RULE_PRINCIPLES}#trailing-question-ban",
            )
        )

    # Rule 6: banned opener
    first = _first_nonempty_line(lines)
    if first:
        for banned in _BANNED_OPENERS:
            if first.startswith(banned):
                breaches.append(
                    Breach(
                        type="banned-opener",
                        sample=first[:120],
                        rule_ref=f"{_RULE_VOICE_MD}#banned-openers",
                    )
                )
                break
        # "Report" as first word (any case)
        first_word = first.split()[0] if first.split() else ""
        if first_word.lower() == "report":
            breaches.append(
                Breach(
                    type="banned-opener",
                    sample=first[:120],
                    rule_ref=f"{_RULE_VOICE_MD}#banned-openers",
                )
            )

    return VoiceCheckResult(passed=len(breaches) == 0, breaches=breaches)
