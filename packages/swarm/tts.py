"""
Text-to-Speech routing for VOLAURA content pipeline.

Providers:
  - **Azure Speech** — native Azerbaijani voices (`az-AZ-BabekNeural` male,
    `az-AZ-BanuNeural` female). Premium path when AZURE_SPEECH_KEY is set.
  - **edge-tts** — FREE Microsoft endpoint serving the SAME az-AZ-BabekNeural
    voice (and ru/en neural voices). Native accent, no key, no cost. Used as the
    AZ/RU/EN fallback so the pipeline never blocks on a missing key.
  - **ElevenLabs Multilingual v2** — premium EN/RU naturalness when its key is set.

Output: 22.05kHz / 16-bit / mono WAV — matches Whisper's preferred input and drops
into Remotion's `<Audio>` via `staticFile()`.

Environment (apps/api/.env, mirrored in GitHub Secrets):
  AZURE_SPEECH_KEY / AZURE_SPEECH_REGION   — optional; enables Azure premium AZ
  ELEVENLABS_API_KEY / ELEVENLABS_VOICE_*  — optional; enables ElevenLabs EN/RU
  (no keys at all → everything routes through free edge-tts)
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


AZURE_VOICES: dict[tuple[Lang, Gender], str] = {
    ("az", "male"): "az-AZ-BabekNeural",
    ("az", "female"): "az-AZ-BanuNeural",
}

# Free fallback via Microsoft edge-tts. For AZ these are the SAME Azure neural
# voices (az-AZ-BabekNeural / BanuNeural) — native accent, no key, no cost.
EDGE_VOICES: dict[tuple[Lang, Gender], str] = {
    ("az", "male"): "az-AZ-BabekNeural",
    ("az", "female"): "az-AZ-BanuNeural",
    ("ru", "male"): "ru-RU-DmitryNeural",
    ("ru", "female"): "ru-RU-SvetlanaNeural",
    ("en", "male"): "en-US-GuyNeural",
    ("en", "female"): "en-US-JennyNeural",
}

# CEO 2026-06-27: edge voices speak too slowly for short-form → speed up.
# edge-tts `rate` accepts a signed percentage, e.g. "+25%". Tune here.
EDGE_RATE = "+25%"

ELEVENLABS_DEFAULT_VOICES: dict[tuple[Lang, Gender], str] = {
    ("en", "male"): "pNInz6obpgDQGcFmaJgB",
    ("en", "female"): "EXAVITQu4vr4xnSDxMaL",
    ("ru", "male"): "pNInz6obpgDQGcFmaJgB",
    ("ru", "female"): "EXAVITQu4vr4xnSDxMaL",
}

ELEVENLABS_MODEL = "eleven_multilingual_v2"


class TTSConfigError(RuntimeError):
    """Missing API key or unsupported (lang, provider) combo."""


class TTSRenderError(RuntimeError):
    """Provider returned a non-200 or empty audio."""


@dataclass
class TTSResult:
    out_path: Path
    provider: Literal["azure", "elevenlabs", "edge", "gemini"]
    voice_id: str
    bytes_written: int


def synthesize(
    text: str,
    lang: Lang,
    out_path: Path,
    gender: Gender = "male",
) -> TTSResult:
    """Render `text` in `lang` to a WAV file at `out_path`.

    AZ: Azure premium if its key is set, else edge-tts (same az-AZ-BabekNeural voice, free).
    EN/RU: ElevenLabs premium if its key is set, else edge-tts free.
    """
    if not text.strip():
        raise ValueError("TTS text is empty")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    if lang == "az":
        if os.environ.get("AZURE_SPEECH_KEY") and os.environ.get("AZURE_SPEECH_REGION"):
            return _synthesize_azure(text, gender=gender, out_path=out_path)
        return _synthesize_edge(text, lang="az", gender=gender, out_path=out_path)
    if lang in ("en", "ru"):
        if os.environ.get("GEMINI_API_KEY"):
            return _synthesize_gemini(text, lang=lang, gender=gender, out_path=out_path)
        if os.environ.get("ELEVENLABS_API_KEY"):
            return _synthesize_elevenlabs(text, lang=lang, gender=gender, out_path=out_path)
        return _synthesize_edge(text, lang=lang, gender=gender, out_path=out_path)

    raise TTSConfigError(f"Unsupported language: {lang}")


def _synthesize_edge(text: str, lang: Lang, gender: Gender, out_path: Path) -> TTSResult:
    """Free neural TTS via Microsoft edge-tts. For AZ this is the SAME
    az-AZ-BabekNeural voice as the Azure path — native accent, zero key, zero cost.
    Transcodes to the 22.05kHz/16-bit/mono WAV the pipeline + Whisper expect."""
    import asyncio
    import subprocess
    try:
        import edge_tts
    except Exception as e:  # pragma: no cover
        raise TTSConfigError("edge-tts not installed (pip install edge-tts)") from e
    voice = EDGE_VOICES[(lang, gender)]
    tmp_mp3 = out_path.with_suffix(".edge.mp3")
    # edge-tts is async. The pipeline calls synthesize() from inside its own
    # running asyncio loop, where asyncio.run() raises "cannot be called from a
    # running event loop". Run the save in a dedicated thread with its own loop
    # so this works both standalone AND inside the pipeline.
    import concurrent.futures

    def _save() -> None:
        asyncio.run(edge_tts.Communicate(text, voice, rate=EDGE_RATE).save(str(tmp_mp3)))

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        ex.submit(_save).result()
    cmd = ["ffmpeg", "-y", "-i", str(tmp_mp3), "-ar", "22050", "-ac", "1",
           "-sample_fmt", "s16", str(out_path)]
    r = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
    try:
        tmp_mp3.unlink()
    except OSError:
        pass
    if r.returncode != 0 or not out_path.is_file():
        raise TTSRenderError(f"edge-tts transcode failed: {r.stderr[-300:]}")
    n = out_path.stat().st_size
    logger.info("edge-tts wrote {bytes}B to {path} (voice={voice})",
                bytes=n, path=str(out_path), voice=voice)
    return TTSResult(out_path=out_path, provider="edge", voice_id=voice, bytes_written=n)


def _synthesize_azure(text: str, gender: Gender, out_path: Path) -> TTSResult:
    api_key = os.environ.get("AZURE_SPEECH_KEY")
    region = os.environ.get("AZURE_SPEECH_REGION")
    if not api_key or not region:
        raise TTSConfigError("AZURE_SPEECH_KEY and AZURE_SPEECH_REGION must be set for AZ TTS")
    voice = AZURE_VOICES[("az", gender)]
    endpoint = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    ssml = (
        '<speak version="1.0" xml:lang="az-AZ">'
        f'<voice xml:lang="az-AZ" name="{voice}">'
        f"{_xml_escape(text)}"
        "</voice></speak>"
    )
    req = request.Request(
        endpoint, method="POST", data=ssml.encode("utf-8"),
        headers={
            "Ocp-Apim-Subscription-Key": api_key,
            "Content-Type": "application/ssml+xml",
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
    logger.info("Azure TTS wrote {bytes} bytes to {path} (voice={voice})",
                bytes=len(audio), path=str(out_path), voice=voice)
    return TTSResult(out_path=out_path, provider="azure", voice_id=voice, bytes_written=len(audio))


# Gemini TTS — CEO 2026-06-27: "use Gemini, it's high quality" (vs free edge).
# Natural, style-directable neural voice. Orus = firm low adult-male (CEO-approved
# earlier). Primary path for EN/RU when GEMINI_API_KEY is set.
GEMINI_TTS_MODELS = ("gemini-3.1-flash-tts-preview", "gemini-2.5-flash-preview-tts")
GEMINI_TTS_VOICE = "Orus"
GEMINI_STYLE_DIRECTIVE = (
    "Read the following in an energetic, upbeat, confident adult male voice at a "
    "lively pace. Do not read these instructions aloud:\n\n"
)


def _synthesize_gemini(text: str, lang: Lang, gender: Gender, out_path: Path) -> TTSResult:
    """Gemini TTS (Orus voice, energy-directed). Returns 24kHz PCM, transcoded to
    the pipeline's 22050/16/mono WAV via ffmpeg. Tries the newest TTS model first."""
    import base64
    import re
    import subprocess

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise TTSConfigError("GEMINI_API_KEY must be set for Gemini TTS")
    try:
        from google import genai
        from google.genai import types
    except Exception as e:  # pragma: no cover
        raise TTSConfigError("google-genai not installed (pip install google-genai)") from e

    client = genai.Client(api_key=api_key)
    cfg = types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=GEMINI_TTS_VOICE),
            ),
        ),
    )
    last_err: Exception | None = None
    for model in GEMINI_TTS_MODELS:
        try:
            resp = client.models.generate_content(
                model=model, contents=GEMINI_STYLE_DIRECTIVE + text, config=cfg,
            )
            part = resp.candidates[0].content.parts[0]
            pcm = part.inline_data.data
            if isinstance(pcm, str):
                pcm = base64.b64decode(pcm)
            if not pcm:
                raise TTSRenderError("Gemini TTS returned empty audio")
            mime = part.inline_data.mime_type or ""
            m = re.search(r"rate=(\d+)", mime)
            rate = int(m.group(1)) if m else 24000

            tmp_wav = out_path.with_suffix(".gem.wav")
            tmp_wav.write_bytes(_wrap_pcm16_as_wav(pcm, sample_rate=rate))
            cmd = ["ffmpeg", "-y", "-i", str(tmp_wav), "-ar", "22050", "-ac", "1",
                   "-sample_fmt", "s16", str(out_path)]
            r = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
            try:
                tmp_wav.unlink()
            except OSError:
                pass
            if r.returncode != 0 or not out_path.is_file():
                raise TTSRenderError(f"Gemini transcode failed: {r.stderr[-300:]}")
            n = out_path.stat().st_size
            logger.info("Gemini TTS wrote {bytes}B to {path} (model={model}, voice={voice})",
                        bytes=n, path=str(out_path), model=model, voice=GEMINI_TTS_VOICE)
            return TTSResult(out_path=out_path, provider="gemini",
                             voice_id=f"{model}:{GEMINI_TTS_VOICE}", bytes_written=n)
        except Exception as e:
            last_err = e
            logger.warning("Gemini TTS model {model} failed: {err}", model=model, err=str(e)[:200])
            continue
    raise TTSRenderError(f"all Gemini TTS models failed: {last_err}")


def _synthesize_elevenlabs(text: str, lang: Lang, gender: Gender, out_path: Path) -> TTSResult:
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise TTSConfigError("ELEVENLABS_API_KEY must be set for EN/RU TTS")
    env_var = f"ELEVENLABS_VOICE_{lang.upper()}"
    voice_id = os.environ.get(env_var) or ELEVENLABS_DEFAULT_VOICES[(lang, gender)]
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
        endpoint, method="POST", data=payload,
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
    wav = _wrap_pcm16_as_wav(pcm, sample_rate=22050)
    out_path.write_bytes(wav)
    logger.info("ElevenLabs TTS wrote {bytes} bytes to {path} (voice={voice}, lang={lang})",
                bytes=len(wav), path=str(out_path), voice=voice_id, lang=lang)
    return TTSResult(out_path=out_path, provider="elevenlabs", voice_id=voice_id, bytes_written=len(wav))


def _xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _json_escape(s: str) -> str:
    import json
    return json.dumps(s, ensure_ascii=False)


def _wrap_pcm16_as_wav(pcm: bytes, sample_rate: int, channels: int = 1) -> bytes:
    import struct
    bits_per_sample = 16
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    data_size = len(pcm)
    header = b"RIFF" + struct.pack("<I", 36 + data_size) + b"WAVE"
    fmt = (
        b"fmt "
        + struct.pack("<I", 16)
        + struct.pack("<H", 1)
        + struct.pack("<H", channels)
        + struct.pack("<I", sample_rate)
        + struct.pack("<I", byte_rate)
        + struct.pack("<H", block_align)
        + struct.pack("<H", bits_per_sample)
    )
    data = b"data" + struct.pack("<I", data_size) + pcm
    return header + fmt + data


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="VOLAURA TTS — Azure/ElevenLabs premium + free edge-tts fallback")
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
        result = synthesize(text=text, lang=args.lang, out_path=Path(args.out), gender=args.gender)
    except (TTSConfigError, TTSRenderError, ValueError) as e:
        logger.error("TTS failed: {err}", err=str(e))
        return 1
    print(f"OK  {result.provider}/{result.voice_id}  {result.bytes_written}B  -> {result.out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
