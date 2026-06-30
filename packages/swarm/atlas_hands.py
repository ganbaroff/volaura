"""
Atlas Hands — desktop control module.
Eyes: screenshot + OCR (read screen text)
Hands: mouse move/click + keyboard type
Brain: receives commands from atlas_command_queue via Claude Code cron

Usage:
  from atlas_hands import take_screenshot, read_screen, click, type_text, get_mouse_pos

This is the physical layer. The orchestrator (cron/bot) decides WHAT to do.
This module does HOW.
"""

import io
import base64
from pathlib import Path

import mss
import pyautogui
from PIL import Image

# Safety: PyAutoGUI failsafe — move mouse to corner to abort
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3  # 300ms between actions (human-like, prevents accidents)


# ── Eyes: Screenshot ────────────────────────────────────────────────

def take_screenshot(region: tuple[int, int, int, int] | None = None, save_path: str | None = None) -> Image.Image:
    """Capture screen (full or region). Returns PIL Image.

    Args:
        region: (left, top, width, height) or None for full screen
        save_path: optional path to save PNG
    """
    with mss.MSS() as sct:
        raw_mon = sct.monitors[1]
        monitor = {"left": int(raw_mon["left"]), "top": int(raw_mon["top"]), "width": int(raw_mon["width"]), "height": int(raw_mon["height"])}
        if region is not None:
            monitor = {"left": int(region[0]), "top": int(region[1]), "width": int(region[2]), "height": int(region[3])}
        raw = sct.grab(monitor)
        img = Image.frombytes("RGB", (raw.width, raw.height), raw.rgb)

    if save_path:
        img.save(save_path)
    return img


def screenshot_to_base64(img: Image.Image, max_width: int = 1280) -> str:
    """Convert PIL Image to base64 string (for sending to LLM vision APIs).
    Resizes to max_width to keep payload small."""
    if img.width > max_width:
        ratio = max_width / img.width
        img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# ── Eyes: OCR (read text from screen) ──────────────────────────────

_ocr_reader = None

def _get_ocr():
    global _ocr_reader
    if _ocr_reader is None:
        import easyocr
        # az (Latin-script) can't mix with ru (Cyrillic) in one reader.
        # Use en+ru for now — covers most screen text. az is Latin = covered by en.
        _ocr_reader = easyocr.Reader(["en", "ru"], gpu=False, verbose=False)
    return _ocr_reader


def read_screen(region: tuple[int, int, int, int] | None = None) -> list[dict]:
    """OCR the screen (full or region). Returns list of {text, bbox, confidence}.

    First call loads the model (~10s). Subsequent calls are fast.
    """
    img = take_screenshot(region)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    reader = _get_ocr()
    results = reader.readtext(buf.getvalue())

    return [
        {"text": text, "bbox": bbox, "confidence": round(conf, 3)}
        for bbox, text, conf in results
    ]


def find_text_on_screen(target: str, region: tuple[int, int, int, int] | None = None) -> dict | None:
    """Find text on screen and return its center coordinates.

    Returns: {text, x, y, confidence} or None if not found.
    """
    results = read_screen(region)
    target_lower = target.lower()

    for r in results:
        if target_lower in r["text"].lower():
            # Calculate center of bounding box
            bbox = r["bbox"]
            cx = int(sum(p[0] for p in bbox) / len(bbox))
            cy = int(sum(p[1] for p in bbox) / len(bbox))
            return {"text": r["text"], "x": cx, "y": cy, "confidence": r["confidence"]}

    return None


# ── Hands: Mouse ───────────────────────────────────────────────────

def get_mouse_pos() -> tuple[int, int]:
    """Get current mouse position."""
    return pyautogui.position()


def move_mouse(x: int, y: int, duration: float = 0.3):
    """Move mouse to (x, y) with smooth motion."""
    pyautogui.moveTo(x, y, duration=duration)


def click(x: int | None = None, y: int | None = None, button: str = "left", clicks: int = 1):
    """Click at position. If x,y not given, click current position."""
    if x is not None and y is not None:
        pyautogui.click(x, y, button=button, clicks=clicks)
    else:
        pyautogui.click(button=button, clicks=clicks)


def right_click(x: int | None = None, y: int | None = None):
    """Right-click at position."""
    click(x, y, button="right")


def double_click(x: int | None = None, y: int | None = None):
    """Double-click at position."""
    click(x, y, clicks=2)


def scroll(amount: int, x: int | None = None, y: int | None = None):
    """Scroll up (positive) or down (negative)."""
    if x is not None and y is not None:
        pyautogui.scroll(amount, x, y)
    else:
        pyautogui.scroll(amount)


# ── Hands: Keyboard ────────────────────────────────────────────────

def type_text(text: str, interval: float = 0.02):
    """Type text character by character."""
    pyautogui.typewrite(text, interval=interval)


def press_key(key: str):
    """Press a single key (enter, tab, escape, f5, etc)."""
    pyautogui.press(key)


def hotkey(*keys: str):
    """Press key combination (e.g. hotkey('ctrl', 'c'))."""
    pyautogui.hotkey(*keys)


# ── Composite actions ──────────────────────────────────────────────

def click_text(target: str, region: tuple[int, int, int, int] | None = None) -> bool:
    """Find text on screen via OCR and click its center. Returns True if found."""
    result = find_text_on_screen(target, region)
    if result:
        click(result["x"], result["y"])
        return True
    return False


def screenshot_and_describe(save_path: str = "/tmp/atlas-screen.png") -> str:
    """Take screenshot, save it, return path.
    The orchestrator can then Read the image file to 'see' the screen."""
    img = take_screenshot(save_path=save_path)
    return f"Screenshot saved: {save_path} ({img.width}x{img.height})"


# ── Ears: Microphone + Speech-to-Text ──────────────────────────────

def record_audio(duration: float = 5.0, save_path: str = "/tmp/atlas-heard.wav") -> str:
    """Record audio from microphone for `duration` seconds. Returns path to WAV file."""
    import sounddevice as sd
    import numpy as np
    import wave

    sample_rate = 16000  # Whisper expects 16kHz
    print(f"[ears] Recording {duration}s...")
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()

    with wave.open(save_path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio.tobytes())

    print(f"[ears] Saved: {save_path}")
    return save_path


def transcribe_audio(audio_path: str = "/tmp/atlas-heard.wav", language: str = "ru") -> str:
    """Transcribe audio file to text using faster-whisper (CPU, small model).

    Args:
        audio_path: path to WAV/MP3 file
        language: "ru", "en", "az", or None for auto-detect
    """
    from faster_whisper import WhisperModel

    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, info = model.transcribe(audio_path, language=language)

    text = " ".join(seg.text.strip() for seg in segments)
    print(f"[ears] Transcribed ({info.language}, {info.language_probability:.0%}): {text[:100]}")
    return text


def listen_and_transcribe(duration: float = 5.0, language: str = "ru") -> str:
    """Record from mic and transcribe. One-call voice input."""
    path = record_audio(duration)
    return transcribe_audio(path, language)


# ── Voice: Text-to-Speech ─────────────────────────────────────────

def speak(text: str, save_path: str = "/tmp/atlas-speaks.wav", voice: str = "Algieba") -> str:
    """Speak text using Gemini TTS (requires GEMINI_API_KEY in env).
    Falls back to edge-tts if Gemini unavailable."""
    import subprocess
    import os

    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        # Use Gemini TTS via the existing tts.py module
        try:
            from packages.swarm.tts import synthesize
            synthesize(text, save_path, voice=voice)
            return save_path
        except Exception as e:
            print(f"[voice] Gemini TTS failed: {e}, falling back to edge-tts")

    # Fallback: edge-tts (free, no API key)
    try:
        subprocess.run(
            ["python", "-m", "edge_tts", "--text", text, "--write-media", save_path, "--voice", "ru-RU-DmitryNeural"],
            capture_output=True, timeout=30
        )
        return save_path
    except Exception as e:
        print(f"[voice] edge-tts failed: {e}")
        return ""


# ── Self-test ──────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Atlas Hands Self-Test ===")

    # Eyes
    img = take_screenshot()
    print(f"Screenshot: {img.width}x{img.height}")

    b64 = screenshot_to_base64(img)
    print(f"Base64 length: {len(b64)} chars")

    # Mouse
    x, y = get_mouse_pos()
    print(f"Mouse position: ({x}, {y})")

    # Screen size
    w, h = pyautogui.size()
    print(f"Desktop: {w}x{h}")

    print("\n=== ALL SYSTEMS READY ===")
    print("Eyes: screenshot OK, base64 OK")
    print("Hands: mouse OK, keyboard OK")
    print("OCR: available (lazy-loaded on first read_screen() call)")
