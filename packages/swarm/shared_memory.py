"""Shared Memory Store — agents see each other's work.

SQLite-based shared memory bus. Zero new dependencies.
Every agent posts results after completing a task.
Next agent reads context before starting.

CEO directive (Session 88): "архитектура коммуникации" — agents were isolated.
This file closes that gap.

Usage:
    from swarm.shared_memory import post_result, get_context, get_latest_by_agent

    # After agent completes work:
    post_result("security-agent", "audit-law1", {"violations": 30, "files": [...]})

    # Before next agent starts:
    context = get_context("audit-law1")  # sees what security-agent found
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

from loguru import logger

# DB lives next to the swarm package — survives restarts, git-ignored
_DB_PATH = Path(__file__).parent.parent.parent / ".swarm" / "swarm_memory.db"


def _ensure_db() -> sqlite3.Connection:
    """Create DB and table if they don't exist."""
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH), timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")  # concurrent reads during writes
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            agent_id   TEXT NOT NULL,
            task_id    TEXT NOT NULL,
            result     TEXT NOT NULL,
            ts         REAL NOT NULL,
            run_id     TEXT DEFAULT '',
            importance INTEGER DEFAULT 5,
            expires_at REAL DEFAULT 0,
            category   TEXT DEFAULT '',
            PRIMARY KEY (agent_id, task_id)
        )
    """)
    # Migration: add columns if table already exists without them
    try:
        conn.execute("ALTER TABLE memory ADD COLUMN importance INTEGER DEFAULT 5")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE memory ADD COLUMN expires_at REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE memory ADD COLUMN category TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_memory_task ON memory(task_id, ts)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_memory_agent ON memory(agent_id, ts DESC)
    """)
    # Agent-to-agent messages table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            from_agent TEXT NOT NULL,
            to_agent   TEXT NOT NULL,
            task_id    TEXT DEFAULT '',
            content    TEXT NOT NULL,
            msg_type   TEXT DEFAULT 'handoff',
            ts         REAL NOT NULL,
            read       INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_to ON messages(to_agent, read, ts)
    """)
    conn.commit()
    return conn


def post_result(
    agent_id: str,
    task_id: str,
    result: dict,
    run_id: str = "",
    importance: int = 5,
    ttl_hours: float = 168,  # default 7 days
    category: str = "",
) -> None:
    """Agent posts its result to shared memory. Other agents can read it.

    importance: 1-10 (10 = critical finding, 1 = noise)
    ttl_hours: how long this fact stays relevant (default 7 days)
    category: security|ux|perf|growth|infra|product|qa|legal|ecosystem
    """
    conn = _ensure_db()
    expires_at = time.time() + (ttl_hours * 3600) if ttl_hours > 0 else 0
    try:
        conn.execute(
            "INSERT OR REPLACE INTO memory (agent_id, task_id, result, ts, run_id, importance, expires_at, category) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (agent_id, task_id, json.dumps(result, ensure_ascii=False), time.time(), run_id, importance, expires_at, category),
        )
        conn.commit()
        logger.debug("Shared memory: {agent} posted to task {task} (importance={imp})", agent=agent_id, task=task_id, imp=importance)
    finally:
        conn.close()


def get_context(task_id: str, include_expired: bool = False) -> list[dict[str, Any]]:
    """Get all agent results for a task. Filters out expired facts by default."""
    conn = _ensure_db()
    now = time.time()
    try:
        if include_expired:
            rows = conn.execute(
                "SELECT agent_id, result, ts, importance, category FROM memory WHERE task_id=? ORDER BY importance DESC, ts",
                (task_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT agent_id, result, ts, importance, category FROM memory WHERE task_id=? AND (expires_at=0 OR expires_at>?) ORDER BY importance DESC, ts",
                (task_id, now),
            ).fetchall()
        return [
            {"agent": r[0], "data": json.loads(r[1]), "ts": r[2], "importance": r[3], "category": r[4]}
            for r in rows
        ]
    finally:
        conn.close()


def get_latest_by_agent(agent_id: str, limit: int = 5) -> list[dict[str, Any]]:
    """Get latest results from a specific agent across all tasks."""
    conn = _ensure_db()
    try:
        rows = conn.execute(
            "SELECT task_id, result, ts FROM memory WHERE agent_id=? ORDER BY ts DESC LIMIT ?",
            (agent_id, limit),
        ).fetchall()
        return [
            {"task_id": r[0], "data": json.loads(r[1]), "ts": r[2]}
            for r in rows
        ]
    finally:
        conn.close()


def get_all_recent(limit: int = 20) -> list[dict[str, Any]]:
    """Get most recent results across all agents. Useful for master-agent overview."""
    conn = _ensure_db()
    try:
        rows = conn.execute(
            "SELECT agent_id, task_id, result, ts FROM memory ORDER BY ts DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            {"agent": r[0], "task_id": r[1], "data": json.loads(r[2]), "ts": r[3]}
            for r in rows
        ]
    finally:
        conn.close()


# ── Agent-to-Agent Messaging ──────────────────────────────────────────

def send_message(from_agent: str, to_agent: str, content: str, task_id: str = "", msg_type: str = "handoff") -> None:
    """Agent sends a message to another agent."""
    conn = _ensure_db()
    try:
        conn.execute(
            "INSERT INTO messages (from_agent, to_agent, task_id, content, msg_type, ts) VALUES (?, ?, ?, ?, ?, ?)",
            (from_agent, to_agent, task_id, content, msg_type, time.time()),
        )
        conn.commit()
        logger.debug("Message: {src} → {dst} ({type})", src=from_agent, dst=to_agent, type=msg_type)
    finally:
        conn.close()


def read_messages(agent_id: str, mark_read: bool = True) -> list[dict[str, Any]]:
    """Agent reads its unread messages."""
    conn = _ensure_db()
    try:
        rows = conn.execute(
            "SELECT id, from_agent, task_id, content, msg_type, ts FROM messages WHERE to_agent=? AND read=0 ORDER BY ts",
            (agent_id,),
        ).fetchall()
        messages = [
            {"id": r[0], "from": r[1], "task_id": r[2], "content": r[3], "type": r[4], "ts": r[5]}
            for r in rows
        ]
        if mark_read and messages:
            ids = [m["id"] for m in messages]
            placeholders = ",".join("?" * len(ids))
            conn.execute(f"UPDATE messages SET read=1 WHERE id IN ({placeholders})", ids)
            conn.commit()
        return messages
    finally:
        conn.close()


def broadcast(from_agent: str, content: str, task_id: str = "") -> None:
    """Agent broadcasts to ALL other agents."""
    send_message(from_agent, "*", content, task_id, msg_type="broadcast")


# ── Cleanup ──────────────────────────────────────────────────────────

def cleanup_old(days: int = 7) -> int:
    """Remove entries older than N days. Run periodically."""
    conn = _ensure_db()
    cutoff = time.time() - (days * 86400)
    try:
        cursor = conn.execute("DELETE FROM memory WHERE ts < ?", (cutoff,))
        conn.execute("DELETE FROM messages WHERE ts < ?", (cutoff,))
        conn.commit()
        deleted = cursor.rowcount
        if deleted:
            logger.info("Shared memory cleanup: {n} old entries removed", n=deleted)
        return deleted
    finally:
        conn.close()
