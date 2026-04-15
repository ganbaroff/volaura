"""Weekly pattern distillation across judged + CEO-decided proposals.

Reads memory/swarm/proposals.json, filters by window (default 30 days) and
ceo_decision != null, groups by agent, clusters titles by keyword, asks ONE
LLM call to summarize accepted vs rejected patterns, writes:

    memory/swarm/distilled-patterns.md   (snapshot — replaced each run)
    memory/atlas/lessons.md              (append-only summary block)

CLI:
    python -m packages.swarm.distiller [--window-days 30]

If no proposal in the window has a ceo_decision (likely on first runs), exits
0 with a clear "skipped — waiting on Telegram action layer" message.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROPOSALS_FILE = PROJECT_ROOT / "memory" / "swarm" / "proposals.json"
PATTERNS_FILE = PROJECT_ROOT / "memory" / "swarm" / "distilled-patterns.md"
LESSONS_FILE = PROJECT_ROOT / "memory" / "atlas" / "lessons.md"

STOPWORDS: set[str] = {
    "the", "a", "an", "and", "or", "but", "for", "of", "to", "in", "on", "at",
    "by", "with", "from", "is", "are", "was", "were", "be", "been", "being",
    "this", "that", "these", "those", "it", "its", "as", "if", "then", "than",
    "not", "no", "yes", "new", "all", "any", "some", "more", "most", "less",
    "also", "still", "only", "without", "added", "missing", "needs", "should",
    "must", "can", "may", "will", "have", "has", "had", "do", "does", "did",
    "via", "per", "into", "onto", "out", "up", "down", "review", "issue",
}


# ── IO helpers ──────────────────────────────────────────────────────────────
def _read_proposals() -> list[dict[str, Any]]:
    if not PROPOSALS_FILE.exists():
        return []
    with open(PROPOSALS_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get("proposals", [])


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".dist-", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _append_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(content)


# ── Filtering + parsing ─────────────────────────────────────────────────────
def _parse_ts(ts: str) -> datetime | None:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _within_window(p: dict[str, Any], window_days: int) -> bool:
    ts = _parse_ts(p.get("timestamp", ""))
    if ts is None:
        return False
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    return ts >= cutoff


def _decision_class(p: dict[str, Any]) -> str | None:
    """Returns 'accepted' / 'rejected' / 'deferred' / None."""
    d = (p.get("ceo_decision") or "").strip().lower()
    if not d:
        return None
    if d in {"accept", "accepted", "yes", "approve", "approved"}:
        return "accepted"
    if d in {"reject", "rejected", "no", "deny", "denied"}:
        return "rejected"
    if d in {"defer", "deferred", "later", "snooze"}:
        return "deferred"
    return d  # treat any other label as a custom class


def _normalize_phrase(title: str) -> tuple[str, ...]:
    """Lowercased, stop-word filtered, length-clipped phrase tuple of 3-5 words."""
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]+", title.lower())
    keep = [w for w in words if w not in STOPWORDS and len(w) > 2]
    return tuple(keep[:5])


# ── Clustering ──────────────────────────────────────────────────────────────
def _cluster(proposals: list[dict[str, Any]], top_k: int = 8) -> list[dict[str, Any]]:
    """Greedy keyword overlap clustering. Cheap, sufficient for v1."""
    clusters: list[dict[str, Any]] = []
    for p in proposals:
        phrase = _normalize_phrase(p.get("title", ""))
        if not phrase:
            continue
        phrase_set = set(phrase)
        placed = False
        for c in clusters:
            overlap = len(phrase_set & c["keywords"])
            if overlap >= max(2, len(phrase_set) // 2):
                c["members"].append(p)
                c["keywords"].update(phrase_set)
                placed = True
                break
        if not placed:
            clusters.append({"keywords": set(phrase_set), "members": [p]})

    # Sort by member count desc, take top_k
    clusters.sort(key=lambda c: -len(c["members"]))
    return clusters[:top_k]


def _cluster_label(c: dict[str, Any]) -> str:
    counts = Counter()
    for p in c["members"]:
        counts.update(_normalize_phrase(p.get("title", "")))
    top = [w for w, _ in counts.most_common(3)]
    return " ".join(top) or "(unlabeled)"


# ── Agent accuracy ──────────────────────────────────────────────────────────
def _agent_accuracy(proposals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_agent: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "proposals": 0, "accepted": 0, "rejected": 0, "deferred": 0,
        "judge_sum": 0.0, "judge_n": 0,
    })
    for p in proposals:
        a = p.get("agent", "unknown")
        row = by_agent[a]
        row["proposals"] += 1
        cls = _decision_class(p)
        if cls in row:
            row[cls] += 1
        js = p.get("judge_score")
        if isinstance(js, (int, float)):
            row["judge_sum"] += float(js)
            row["judge_n"] += 1

    out = []
    for agent, row in by_agent.items():
        decided = row["accepted"] + row["rejected"]
        accuracy = (row["accepted"] / decided) if decided else 0.0
        avg_judge = (row["judge_sum"] / row["judge_n"]) if row["judge_n"] else 0.0
        out.append({
            "agent": agent,
            "proposals": row["proposals"],
            "accepted": row["accepted"],
            "rejected": row["rejected"],
            "deferred": row["deferred"],
            "judge_avg": round(avg_judge, 2),
            "accuracy": round(accuracy, 2),
        })
    out.sort(key=lambda r: -r["accuracy"])
    return out


# ── LLM summary (single call) ───────────────────────────────────────────────
async def _llm_summarize(grouped: dict[str, list[dict[str, Any]]]) -> str:
    """One call to llm_router. Returns plain text with 6 bullets."""
    try:
        from packages.swarm.tools.llm_router import llm_completion
    except ImportError:
        from swarm.tools.llm_router import llm_completion  # type: ignore

    # Compact serialization for the LLM
    def _fmt(items: list[dict[str, Any]]) -> str:
        lines = []
        for p in items[:30]:
            lines.append(
                f"- [{p.get('agent','?')}] "
                f"{(p.get('title','') or '')[:120]} "
                f"(judge={p.get('judge_score')}, decision={p.get('ceo_decision')})"
            )
        return "\n".join(lines) or "(none)"

    payload = (
        "ACCEPTED PROPOSALS:\n"
        f"{_fmt(grouped.get('accepted', []))}\n\n"
        "REJECTED PROPOSALS:\n"
        f"{_fmt(grouped.get('rejected', []))}\n\n"
        "DEFERRED PROPOSALS:\n"
        f"{_fmt(grouped.get('deferred', []))}\n"
    )

    system = (
        "You summarize a list of proposal outcomes into exactly 3 "
        "accepted-pattern bullets and exactly 3 rejected-pattern bullets, "
        "one sentence each, concrete and action-actionable. Output format:\n"
        "ACCEPTED:\n- ...\n- ...\n- ...\nREJECTED:\n- ...\n- ...\n- ...\n"
        "No prose around the lists."
    )
    try:
        return await llm_completion(payload, system=system, max_tokens=400)
    except Exception as e:
        logger.warning("LLM summary failed: {e}", e=e)
        return "ACCEPTED:\n- (LLM summary unavailable)\nREJECTED:\n- (LLM summary unavailable)\n"


# ── Markdown rendering ──────────────────────────────────────────────────────
def _render_patterns_md(
    window_days: int,
    decided: list[dict[str, Any]],
    grouped: dict[str, list[dict[str, Any]]],
    accepted_clusters: list[dict[str, Any]],
    rejected_clusters: list[dict[str, Any]],
    accuracy: list[dict[str, Any]],
    llm_summary: str,
) -> str:
    today = datetime.now(timezone.utc).date().isoformat()
    out: list[str] = []
    out.append(f"# Distilled patterns — week of {today}")
    out.append("")
    out.append(
        f"Window: last {window_days} days · "
        f"Decided proposals: {len(decided)} "
        f"(accepted={len(grouped.get('accepted',[]))}, "
        f"rejected={len(grouped.get('rejected',[]))}, "
        f"deferred={len(grouped.get('deferred',[]))})"
    )
    out.append("")

    out.append("## Accepted patterns (CEO said yes, judge score >= 7)")
    if not accepted_clusters:
        out.append("- (none yet)")
    for c in accepted_clusters:
        label = _cluster_label(c)
        agents = sorted({m.get("agent", "?") for m in c["members"]})
        ex = c["members"][0]
        out.append(
            f"- **{label}** — {len(c['members'])} proposals from "
            f"[{', '.join(agents)}]. Common thread: {(ex.get('title','') or '')[:120]}. "
            f"Example: #{ex.get('id','?')}"
        )
    out.append("")

    out.append("## Rejected patterns (CEO said no OR judge score <= 4)")
    if not rejected_clusters:
        out.append("- (none yet)")
    for c in rejected_clusters:
        label = _cluster_label(c)
        agents = sorted({m.get("agent", "?") for m in c["members"]})
        ex = c["members"][0]
        out.append(
            f"- **{label}** — {len(c['members'])} rejections from "
            f"[{', '.join(agents)}]. Common thread: {(ex.get('title','') or '')[:120]}. "
            f"Example: #{ex.get('id','?')}"
        )
    out.append("")

    out.append(f"## Agent accuracy (rolling last {window_days} days)")
    out.append("| Agent | Proposals | Accepted | Rejected | Judge avg | Accuracy |")
    out.append("|---|---|---|---|---|---|")
    for r in accuracy:
        out.append(
            f"| {r['agent']} | {r['proposals']} | {r['accepted']} | "
            f"{r['rejected']} | {r['judge_avg']} | {r['accuracy']} |"
        )
    out.append("")

    out.append("## New rules extracted this week")
    out.append("")
    out.append(llm_summary.strip())
    out.append("")
    out.append("_Promote any rule recurring 3+ weeks to memory/atlas/lessons.md._")
    out.append("")

    return "\n".join(out)


def _render_lessons_block(
    decided: list[dict[str, Any]],
    grouped: dict[str, list[dict[str, Any]]],
    accuracy: list[dict[str, Any]],
    llm_summary: str,
) -> str:
    today = datetime.now(timezone.utc).date().isoformat()
    n = len(decided)
    k = len(grouped.get("accepted", []))
    r = len(grouped.get("rejected", []))
    d = len(grouped.get("deferred", []))

    # Parse 3 accepted + 3 rejected one-liners from the LLM summary
    def _extract(section: str, text: str) -> list[str]:
        m = re.search(rf"{section}:\s*(.*?)(?:\n[A-Z]+:|\Z)", text, re.S | re.I)
        if not m:
            return []
        return [
            line.lstrip("-* ").strip()
            for line in m.group(1).splitlines()
            if line.strip().startswith(("-", "*"))
        ]

    acc_lines = _extract("ACCEPTED", llm_summary)[:3]
    rej_lines = _extract("REJECTED", llm_summary)[:3]

    improved = [a["agent"] for a in accuracy if a["accuracy"] >= 0.7][:5]
    flagged = [
        a["agent"] for a in accuracy
        if (a["accepted"] + a["rejected"]) >= 2 and a["accuracy"] < 0.5
    ][:5]

    return (
        "\n"
        f"## {today} — Weekly swarm distillation\n"
        f"This week the swarm proposed {n} things. "
        f"CEO accepted {k}, rejected {r}, deferred {d}. "
        f"Patterns that worked: {'; '.join(acc_lines) or '(none)'}. "
        f"Patterns to stop: {'; '.join(rej_lines) or '(none)'}. "
        f"Agents whose accuracy improved: "
        f"{', '.join(improved) if improved else '(none)'}. "
        f"Agents flagged for prompt revision: "
        f"{', '.join(flagged) if flagged else '(none)'}.\n"
    )


# ── Main ────────────────────────────────────────────────────────────────────
async def main_async(window_days: int) -> int:
    proposals = _read_proposals()
    in_window = [p for p in proposals if _within_window(p, window_days)]
    decided = [p for p in in_window if _decision_class(p) is not None]

    if not decided:
        msg = (
            "No CEO-decided proposals in window. Distillation skipped. "
            "Waiting on Telegram action-layer implementation."
        )
        logger.info(msg)
        sys.stdout.write(msg + "\n")
        return 0

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for p in decided:
        cls = _decision_class(p) or "other"
        grouped[cls].append(p)

    # Judge-score-based pseudo decisions for clustering surface
    accepted_for_cluster = [
        p for p in grouped.get("accepted", [])
        if (p.get("judge_score") or 0) >= 7
    ] or grouped.get("accepted", [])
    rejected_for_cluster = list(grouped.get("rejected", [])) + [
        p for p in in_window
        if isinstance(p.get("judge_score"), (int, float))
        and p["judge_score"] <= 4
        and _decision_class(p) != "accepted"
    ]

    accepted_clusters = _cluster(accepted_for_cluster)
    rejected_clusters = _cluster(rejected_for_cluster)
    accuracy = _agent_accuracy(in_window)
    llm_summary = await _llm_summarize(grouped)

    patterns_md = _render_patterns_md(
        window_days, decided, grouped,
        accepted_clusters, rejected_clusters, accuracy, llm_summary,
    )
    _atomic_write_text(PATTERNS_FILE, patterns_md)
    logger.info("Wrote {p}", p=PATTERNS_FILE)

    lessons_block = _render_lessons_block(decided, grouped, accuracy, llm_summary)
    _append_text(LESSONS_FILE, lessons_block)
    logger.info("Appended weekly block to {p}", p=LESSONS_FILE)

    sys.stdout.write(
        f"Distilled {len(decided)} decided proposals "
        f"(window={window_days}d). Patterns updated.\n"
    )
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Weekly swarm pattern distiller")
    parser.add_argument("--window-days", type=int, default=30)
    args = parser.parse_args()
    rc = asyncio.run(main_async(window_days=args.window_days))
    sys.exit(rc)


if __name__ == "__main__":
    main()
