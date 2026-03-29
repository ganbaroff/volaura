#!/usr/bin/env python3
"""
Jarvis Daemon — "Hey Jarvis" voice-activated PC controller for the VOLAURA ecosystem.

Detection pipeline:
  microphone → openwakeword ("hey_jarvis") → faster-whisper STT → Groq NLU → action executor

Supported actions:
  PC control  — open apps, type text, open URLs, screenshot
  ZEUS hooks  — trigger content generation, launch swarm
  System      — lock screen, search web

Install (run once):
    pip install openwakeword faster-whisper pyaudio pyautogui groq python-dotenv loguru numpy
    # Windows PyAudio wheel (if pip install pyaudio fails):
    #   pip install pipwin && pipwin install pyaudio
    # OR download from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

First run downloads openwakeword "hey_jarvis" model (~15MB) from GitHub releases.
Whisper "base" model (~140MB) downloads automatically via faster-whisper.

Run:
    python -m packages.swarm.jarvis_daemon          # from VOLAURA root
    python packages/swarm/jarvis_daemon.py          # directly
    # Or use: scripts/start_jarvis.bat
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from queue import Empty, Queue
from threading import Thread

from dotenv import load_dotenv
from loguru import logger

# ── Path setup ────────────────────────────────────────────────
project_root = Path(__file__).parent.parent.parent
packages_path = str(project_root / "packages")
if packages_path not in sys.path:
    sys.path.insert(0, packages_path)

load_dotenv(project_root / "apps" / "api" / ".env")

# ── Optional imports (warn, don't crash) ──────────────────────
try:
    import numpy as np
    NUMPY_OK = True
except ImportError:
    NUMPY_OK = False
    logger.error("numpy not installed. Run: pip install numpy")

try:
    import pyaudio
    PYAUDIO_OK = True
except ImportError:
    PYAUDIO_OK = False
    logger.error("pyaudio not installed. Run: pip install pyaudio")

try:
    import openwakeword  # type: ignore[import]
    from openwakeword.model import Model as WakeModel  # type: ignore[import]
    OWW_OK = True
except ImportError:
    OWW_OK = False
    logger.error("openwakeword not installed. Run: pip install openwakeword")

try:
    from faster_whisper import WhisperModel  # type: ignore[import]
    WHISPER_OK = True
except ImportError:
    WHISPER_OK = False
    logger.error("faster-whisper not installed. Run: pip install faster-whisper")

try:
    import pyautogui  # type: ignore[import]
    pyautogui.FAILSAFE = True
    PYAUTOGUI_OK = True
except ImportError:
    PYAUTOGUI_OK = False
    logger.warning("pyautogui not installed — type/screenshot actions disabled. Run: pip install pyautogui")

# ── Audio constants ────────────────────────────────────────────
SAMPLE_RATE     = 16_000     # Hz — required by openwakeword + Whisper
CHUNK_SIZE      = 1_280      # 80ms chunks @ 16kHz (openwakeword requirement)
CHANNELS        = 1

WAKE_WORD       = "hey_jarvis"
WAKE_THRESHOLD  = 0.5        # 0.0–1.0 sensitivity

MAX_RECORD_SEC  = 7          # max seconds to record after wake word
SILENCE_RMS     = 400        # RMS below this = silence
SILENCE_CHUNKS  = 18         # ~1.4s of silence → stop recording

# ── NLU ───────────────────────────────────────────────────────
GROQ_MODEL = "llama-3.3-70b-versatile"

NLU_SYSTEM = """You parse voice commands (Russian or English) into JSON actions.
Return ONLY valid JSON, no extra text.

Schema:
{
  "action": "open_app|type_text|open_url|search|screenshot|zeus_content|zeus_swarm|lock|unknown",
  "params": {
    "app":     "<executable name, if open_app>",
    "text":    "<text to type, if type_text>",
    "url":     "<URL, if open_url>",
    "query":   "<search query, if search>",
    "channel": "<volaura|brandedby|mindshift|ecosystem, if zeus_content>",
    "mode":    "<daily-ideation|code-review|cto-audit, if zeus_swarm>"
  },
  "response": "<spoken confirmation, max 8 words>"
}

Russian shortcuts: открой=open_app, напиши=type_text, найди=search,
опубликуй/telegram=zeus_content, рой/агент/swarm=zeus_swarm, скриншот=screenshot"""

APP_MAP: dict[str, str] = {
    "chrome":          "chrome",
    "браузер":         "chrome",
    "browser":         "chrome",
    "notepad":         "notepad",
    "блокнот":         "notepad",
    "explorer":        "explorer",
    "проводник":       "explorer",
    "terminal":        "cmd",
    "терминал":        "cmd",
    "powershell":      "powershell",
    "vs code":         "code",
    "vscode":          "code",
    "код":             "code",
    "spotify":         "spotify",
    "calculator":      "calc",
    "калькулятор":     "calc",
    "task manager":    "taskmgr",
    "диспетчер":       "taskmgr",
    "telegram":        "telegram",
}


class JarvisDaemon:
    """Background daemon: listens for 'Hey Jarvis', understands commands, acts."""

    def __init__(self) -> None:
        self._audio_q: Queue[bytes] = Queue()
        self._wake_model: WakeModel | None = None
        self._whisper: WhisperModel | None = None
        self._groq_key = os.environ.get("GROQ_API_KEY", "")
        self._running = False

    # ─────────────────────────────────────────────────────────
    # Bootstrap
    # ─────────────────────────────────────────────────────────

    def _load_models(self) -> bool:
        missing = []
        if not NUMPY_OK:   missing.append("numpy")
        if not PYAUDIO_OK: missing.append("pyaudio")
        if not OWW_OK:     missing.append("openwakeword")
        if not WHISPER_OK: missing.append("faster-whisper")
        if missing:
            logger.error(f"Install missing packages: pip install {' '.join(missing)}")
            return False

        logger.info("Loading Whisper base model (downloads ~140MB on first run)...")
        self._whisper = WhisperModel("base", device="cpu", compute_type="int8")

        logger.info(f"Loading openwakeword '{WAKE_WORD}' (downloads ~15MB on first run)...")
        try:
            self._wake_model = WakeModel(
                wakeword_models=[WAKE_WORD],
                inference_framework="onnx",
            )
        except Exception:
            logger.info("Downloading wake-word model from GitHub...")
            openwakeword.utils.download_models([WAKE_WORD])
            self._wake_model = WakeModel(
                wakeword_models=[WAKE_WORD],
                inference_framework="onnx",
            )

        logger.success("Models ready.")
        return True

    # ─────────────────────────────────────────────────────────
    # Audio capture (background thread)
    # ─────────────────────────────────────────────────────────

    def _mic_thread(self) -> None:
        pa = pyaudio.PyAudio()
        stream = pa.open(
            rate=SAMPLE_RATE,
            channels=CHANNELS,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
        )
        logger.info("Microphone open. Listening for 'Hey Jarvis'...")
        try:
            while self._running:
                chunk = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                self._audio_q.put(chunk)
        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()

    # ─────────────────────────────────────────────────────────
    # Wake word detection
    # ─────────────────────────────────────────────────────────

    def _check_wake(self) -> bool:
        try:
            chunk = self._audio_q.get(timeout=0.3)
        except Empty:
            return False
        audio = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0
        scores = self._wake_model.predict(audio)  # type: ignore[union-attr]
        return float(scores.get(WAKE_WORD, 0.0)) >= WAKE_THRESHOLD

    # ─────────────────────────────────────────────────────────
    # Record command after wake word
    # ─────────────────────────────────────────────────────────

    def _record_command(self) -> bytes:
        logger.info("Wake word! Listening for command...")
        # Drain stale audio
        while not self._audio_q.empty():
            self._audio_q.get_nowait()

        frames: list[bytes] = []
        silence = 0
        max_chunks = int(SAMPLE_RATE / CHUNK_SIZE * MAX_RECORD_SEC)

        for _ in range(max_chunks):
            try:
                chunk = self._audio_q.get(timeout=0.5)
            except Empty:
                break
            frames.append(chunk)
            rms = float(np.sqrt(np.mean(np.frombuffer(chunk, dtype=np.int16).astype(np.float32) ** 2)))
            silence = silence + 1 if rms < SILENCE_RMS else 0
            if silence >= SILENCE_CHUNKS:
                break

        return b"".join(frames)

    # ─────────────────────────────────────────────────────────
    # STT — faster-whisper (local, offline)
    # ─────────────────────────────────────────────────────────

    def _transcribe(self, audio_bytes: bytes) -> str:
        if not audio_bytes:
            return ""
        audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        # language=None → auto-detect (handles Russian + English mix)
        segments, _ = self._whisper.transcribe(audio, language=None, beam_size=1)  # type: ignore[union-attr]
        text = " ".join(s.text for s in segments).strip()
        logger.info(f"Heard: '{text}'")
        return text

    # ─────────────────────────────────────────────────────────
    # NLU — Groq (fast, structured JSON)
    # ─────────────────────────────────────────────────────────

    async def _parse(self, text: str) -> dict:
        if not text:
            return {"action": "unknown", "params": {}, "response": "I didn't catch that"}

        if not self._groq_key:
            return self._keyword_parse(text)

        try:
            from groq import AsyncGroq
            client = AsyncGroq(api_key=self._groq_key)
            resp = await asyncio.wait_for(
                client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": NLU_SYSTEM},
                        {"role": "user", "content": text},
                    ],
                    temperature=0.1,
                    max_tokens=200,
                    response_format={"type": "json_object"},
                ),
                timeout=5.0,
            )
            return json.loads(resp.choices[0].message.content or "{}")
        except Exception as e:
            logger.warning(f"Groq NLU failed ({e}), using keyword fallback")
            return self._keyword_parse(text)

    def _keyword_parse(self, text: str) -> dict:
        t = text.lower()
        for kw in ("открой", "запусти", "open", "launch"):
            if kw in t:
                for alias, exe in APP_MAP.items():
                    if alias in t:
                        return {"action": "open_app", "params": {"app": exe}, "response": f"Opening {alias}"}
        if any(w in t for w in ("скриншот", "screenshot")):
            return {"action": "screenshot", "params": {}, "response": "Screenshot saved"}
        if any(w in t for w in ("найди", "search", "google")):
            query = text.split("найди")[-1].split("search")[-1].strip()
            return {"action": "search", "params": {"query": query}, "response": f"Searching {query}"}
        if any(w in t for w in ("телеграм", "telegram", "опубликуй", "publish")):
            return {"action": "zeus_content", "params": {"channel": "ecosystem"}, "response": "Posting to Telegram"}
        if any(w in t for w in ("рой", "агент", "swarm")):
            return {"action": "zeus_swarm", "params": {"mode": "daily-ideation"}, "response": "Launching swarm"}
        if any(w in t for w in ("lock", "заблокируй", "блокировка")):
            return {"action": "lock", "params": {}, "response": "Locking screen"}
        return {"action": "unknown", "params": {}, "response": "Command not understood"}

    # ─────────────────────────────────────────────────────────
    # Action executor
    # ─────────────────────────────────────────────────────────

    async def _execute(self, cmd: dict) -> None:
        action  = cmd.get("action", "unknown")
        params  = cmd.get("params", {})
        response = cmd.get("response", "")
        logger.info(f"Action: {action} | {params} | '{response}'")

        if action == "open_app":
            app = params.get("app", "")
            if app:
                subprocess.Popen(app, shell=True)

        elif action == "type_text" and PYAUTOGUI_OK:
            await asyncio.sleep(0.4)
            pyautogui.typewrite(params.get("text", ""), interval=0.04)

        elif action == "open_url":
            webbrowser.open(params.get("url", ""))

        elif action == "search":
            q = params.get("query", "")
            webbrowser.open(f"https://www.google.com/search?q={q.replace(' ', '+')}")

        elif action == "screenshot":
            if PYAUTOGUI_OK:
                shots_dir = project_root / "assets" / "screenshots"
                shots_dir.mkdir(parents=True, exist_ok=True)
                path = shots_dir / f"jarvis_{int(time.time())}.png"
                pyautogui.screenshot(str(path))
                logger.success(f"Screenshot: {path}")
            else:
                logger.warning("pyautogui not installed — screenshot unavailable")

        elif action == "zeus_content":
            await self._zeus_content(params.get("channel", ""))

        elif action == "zeus_swarm":
            await self._zeus_swarm(params.get("mode", "daily-ideation"))

        elif action == "lock":
            subprocess.Popen("rundll32.exe user32.dll,LockWorkStation", shell=True)

        else:
            logger.info("Unrecognized command — try 'Hey Jarvis, open Chrome'")

    # ─────────────────────────────────────────────────────────
    # ZEUS integration
    # ─────────────────────────────────────────────────────────

    async def _zeus_content(self, channel: str) -> None:
        """Trigger ZEUS content engine (non-blocking subprocess)."""
        logger.info(f"ZEUS: scheduled content run ({channel or 'all channels'})")
        cmd = [sys.executable, "-m", "packages.swarm.zeus_content_run", "--mode=scheduled"]
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.Popen(cmd, cwd=str(project_root)),
        )

    async def _zeus_swarm(self, mode: str) -> None:
        """Launch the VOLAURA MiroFish autonomous swarm."""
        logger.info(f"ZEUS: launching swarm (mode={mode})")
        cmd = [sys.executable, "-m", "packages.swarm.autonomous_run", f"--mode={mode}"]
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.Popen(cmd, cwd=str(project_root)),
        )

    # ─────────────────────────────────────────────────────────
    # Main loop
    # ─────────────────────────────────────────────────────────

    async def run(self) -> None:
        if not self._load_models():
            return

        self._running = True
        Thread(target=self._mic_thread, daemon=True).start()

        logger.success("Jarvis daemon running. Say 'Hey Jarvis' to activate.")

        try:
            while self._running:
                if self._check_wake():
                    audio  = self._record_command()
                    text   = self._transcribe(audio)
                    if text:
                        cmd = await self._parse(text)
                        await self._execute(cmd)
                        logger.info("Ready. Listening again...")
                await asyncio.sleep(0.01)
        except KeyboardInterrupt:
            logger.info("Jarvis stopped (Ctrl+C).")
        finally:
            self._running = False


def main() -> None:
    asyncio.run(JarvisDaemon().run())


if __name__ == "__main__":
    main()
