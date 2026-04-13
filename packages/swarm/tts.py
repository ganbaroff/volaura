"""
Text-to-Speech routing for VOLAURA content pipeline.

Why two providers:
  - **Azure Speech** is the ONLY production-grade TTS with native Azerbaijani voices
    (`az-AZ-BabekNeural` male, `az-AZ-BanuNeural` female). ElevenLabs v3 supports AZ
    text but renders it with English-accent bleed — disqualifying for AZ-first content
    (Constitution: AZ is the canonical voice of the brand).
  - **ElevenLabs Multilingual v2/v3** wins for EN + RU on naturalness, expressiveness,
    and prosody. We pin a single voice ID per language so weekly batches stay
    sonically consistent.

Output: 22.05kHz / 16-bit / mono WAV in `apps/web/public/voiceovers/` —
matches Whisper's preferred input, drops directly into Remotion's `<Audio>` via
`staticFile()`.

Environment (set in `apps/api/.env`, mirrored in GitHub Secrets):
  AZURE_SPEECH_KEY        — region-bound subscription key
  AZURE_SPEECH_REGION     — e.g. "westeurope"
  ELEVENLABS_API_KEY      — sk_...
  ELEVENLABS_VOICE_EN     — voice_id for English
  ELEVENLABS_VOICE_RU     — voice_id for Russian

Usage (CLI):
    python -m packages.swarm.tts \
        --lang az --text "Salam, mən VOLAURA-dan." \
        --out apps/web/public/voiceovers/post-2026-04-13.wav

Usage (Python):
    from packages.swarm.tts import synthesize
    synthesize(text="Hello", lang="en", out_path=Path("voiceover.wav"))
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib import error, request

from loguru import logger

Lang = Literal["az", "en", "ru"]
Gender = Literal["male", "female"]


# ──────────────────────────────────────────────────────────────────────────
# Voice registry — pinned per Constitution (one voice per lang per gender)
# ──────────────────────────────────────────────────────────────────────────

AZURE_VOICES: dict[tuple[Lang, Gender], str] = {
    ("az", "male"): "az-AZ-BabekNeural",
    ("az", "female"): "az-AZ-BanuNeural",
}

# ElevenLabs voice IDs are read from env so they can be A/B-rotated without
# code changes. Defaults below are well-known stock voices that work today.
ELEVENLABS_DEFAULT_VOICES: dict[tuple[Lang, Gender], str] = {
    ("en", "male"): "pNInz6obpgDQGcFmaJgB",  # Adam — neutral US male
    ("en", "female"): "EXAVITQu4vr4xnSDxMaL",  # Bella — warm US female
    ("ru", "male"): "pNInz6obpgDQGcFmaJgB",   # Adam — multilingual v2/v3
    ("ru", "female"): "EXAVITQu4vr4xnSDxMaL",  # Bella — multilingual v2/v3
}

ELEVENLABS_MODEL = "eleven_multilingual_v2"


# ──────────────────────────────────────────────────────────────────────────
# Errors
# ──────────────────────────────────────────────────────────────────────────


class TTSConfigError(RuntimeError):
    """Missing API key or unsupported (lang, provider) combo."""


class TTSRenderError(RuntimeError):
    """Provider returned a non-200 or empty audio."""


# ──────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────


@dataclass
class TTSResult:
    out_path: Path
    provider: Literal["azure", "elevenlabs"]
    voice_id: str
    bytes_written: int


def synthesize(
    text: str,
    lang: Lang,
    out_path: Path,
    gender: Gender = "male",
) -> TTSResult:
    """Render `text` in `lang` to a WAV file at `out_path`.

    Routes:
      lang == "az"    → Azure (native AZ accent — only acceptable choice)
      lang in ("en","ru") → ElevenLabs Multilingual v2 (best naturalness)
    """
    if not text.strip():
        raise ValueError("TTS text is empty")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    if lang == "az":
        return _synthesize_azure(text, gender=gender, out_path=out_path)
    if lang in ("en", "ru"):
        return _synthesize_elevenlabs(text, lang=lang, gender=gender, out_path=out_path)

    raise TTSConfigError(f"Unsupported language: {lang}")


# ──────────────────────────────────────────────────────────────────────────
# Azure Speech (AZ)
# ──────────────────────────────────────────────────────────────────────────


def _synthesize_azure(text: str, gender: Gender, out_path: Path) -> TTSResult:
    api_key = os.environ.get("AZURE_SPEECH_KEY")
    region = os.environ.get("AZURE_SPEECH_REGION")
    if not api_key or not region:
        raise TTSConfigError(
            "AZURE_SPEECH_KEY and AZURE_SPEECH_REGION must be set for AZ TTS",
        )

    voice = AZURE_VOICES[("az", gender)]
    endpoint = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"

    # SSML keeps prosody control if we ever need rate/pitch adjustments per beat.
    ssml = (
        '<speak version="1.0" xml:lang="az-AZ">'
        f'<voice xml:lang="az-AZ" name="{voice}">'
        f"{_xml_escape(text)}"
        "</voice></speak>"
    )

    req = request.Request(
        endpoint,
        method="POST",
        data=ssml.encode("utf-8"),
        headers={
            "Ocp-Apim-Subscription-Key": api_key,
            "Content-Type": "application/ssml+xml",
            # 22.05kHz 16-bit mono PCM RIFF — matches Whisper-friendly input
            "X-Microsoft-OutputFormat": "riff-22050hz-16bit-mono-pcm",
            "User-Agent": "volaura-swarm-tts/1.0",
        },
    )

    try:
        with request.urlopen(req, timeout=60) as resp:
            audio = resp.read()
    except error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise TTSRenderError(f"Azure TTS HTTP {e.code}: {body}") from e
    except error.URLError as e:
        raise TTSRenderError(f"Azure TTS network error: {e.reason}") from e

    if not audio:
        raise TTSRenderError("Azure TTS returned empty body")

    out_path.write_bytes(audio)
    logger.info(
        "Azure TTS wrote {bytes} bytes to {path} (voice={voice})",
        bytes=len(audio),
        path=str(out_path),
        voice=voice,
    )
    return TTSResult(
        out_path=out_path, provider="azure", voice_id=voice, bytes_written=len(audio),
    )


# ──────────────────────────────────────────────────────────────────────────
# ElevenLabs (EN, RU)
# ──────────────────────────────────────────────────────────────────────────


def _synthesize_elevenlabs(
    text: str, lang: Lang, gender: Gender, out_path: Path,
) -> TTSResult:
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise TTSConfigError("ELEVENLABS_API_KEY must be set for EN/RU TTS")

    # Allow per-language env override; fall back to defaults
    env_var = f"ELEVENLABS_VOICE_{lang.upper()}"
    voice_id = os.environ.get(env_var) or ELEVENLABS_DEFAULT_VOICES[(lang, gender)]

    # ElevenLabs returns MP3 by default; request PCM16 22.05kHz so it lines up
    # with Azure output and Whisper expectations.
    output_format = "pcm_22050"
    endpoint = (
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        f"?output_format={output_format}"
    )

    payload = (
        '{"text":' + _json_escape(text)
        + ',"model_id":"' + ELEVENLABS_MODEL + '"'
        + ',"voice_settings":{"stability":0.5,"similarity_boost":0.75}}'
    ).encode("utf-8")

    req = request.Request(
        endpoint,
        method="POST",
        data=payload,
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/wav",
            "User-Agent": "volaura-swarm-tts/1.0",
        },
    )

    try:
        with request.urlopen(req, timeout=120) as resp:
            pcm = resp.read()
    except error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise TTSRenderError(f"ElevenLabs HTTP {e.code}: {body}") from e
    except error.URLError as e:
        raise TTSRenderError(f"ElevenLabs network error: {e.reason}") from e

    if not pcm:
        raise TTSRenderError("ElevenLabs returned empty body")

    # ElevenLabs `pcm_22050` returns raw little-endian int16 samples. Wrap into
    # a RIFF/WAV header so Remotion's `<Audio>` can play it directly without a
    # ffmpeg pass.
    wav = _wrap_pcm16_as_wav(pcm, sample_rate=22050)
    out_path.write_bytes(wav)
    logger.info(
        "ElevenLabs TTS wrote {bytes} bytes to {path} (voice={voice}, lang={lang})",
        bytes=len(wav),
        path=str(out_path),
        voice=voice_id,
        lang=lang,
    )
    return TTSResult(
        out_path=out_path,
        provider="elevenlabs",
        voice_id=voice_id,
        bytes_written=len(wav),
    )


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────


def _xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _json_escape(s: str) -> str:
    """Stdlib-only JSON string escape (we already build the rest by hand)."""
    import json

    return json.dumps(s, ensure_ascii=False)


def _wrap_pcm16_as_wav(pcm: bytes, sample_rate: int, channels: int = 1) -> bytes:
    """Wrap raw 16-bit PCM samples in a RIFF WAV container."""
    import struct

    bits_per_sample = 16
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    data_size = len(pcm)

    header = b"RIFF" + struct.pack("<I", 36 + data_size) + b"WAVE"
    fmt = (
        b"fmt "
        + struct.pack("<I", 16)            # PCM chunk size
        + struct.pack("<H", 1)             # audio format = PCM
        + struct.pack("<H", channels)
        + struct.pack("<I", sample_rate)
        + struct.pack("<I", byte_rate)
        + struct.pack("<H", block_align)
        + struct.pack("<H", bits_per_sample)
    )
    data = b"data" + struct.pack("<I", data_size) + pcm
    return header + fmt + data


# ──────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="VOLAURA TTS — Azure (AZ) + ElevenLabs (EN/RU)")
    parser.add_argument("--lang", required=True, choices=["az", "en", "ru"])
    parser.add_argument("--gender", default="male", choices=["male", "female"])
    parser.add_argument("--text", help="Inline text to synthesize")
    parser.add_argument("--text-file", help="Path to UTF-8 text file (overrides --text)")
    parser.add_argument("--out", required=True, help="Output WAV path")
    args = parser.parse_args(argv)

    if args.text_file:
        text = Path(args.text_file).read_text(encoding="utf-8")
    elif args.text:
        text = args.text
    else:
        parser.error("Must provide --text or --text-file")
        return 2

    try:
        result = synthesize(
            text=text,
            lang=args.lang,
            out_path=Path(args.out),
            gender=args.gender,
        )
    except (TTSConfigError, TTSRenderError, ValueError) as e:
        logger.error("TTS failed: {err}", err=str(e))
        return 1

    print(f"OK  {result.provider}/{result.voice_id}  {result.bytes_written}B  -> {result.out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
