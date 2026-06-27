# Session Handoff — Video Content Pipeline Phase 0

**Date:** 2026-06-27  
**Author:** Atlas (coder subagent)  
**Status:** Phase 0 implemented — proof run pending credentials

---

## What shipped

End-to-end Phase 0 scaffold: script → TTS WAV → Whisper captions → ReactionDuet MP4 → manifest/PROOF.md → Telegram (if creds).

| Component | Path |
|-----------|------|
| ReactionDuet composition | `packages/remotion/src/compositions/ReactionDuet.tsx` |
| Dynamic duration metadata | `packages/remotion/src/compositions/reaction-duet-metadata.ts` |
| Post #2 data | `packages/remotion/src/data/reaction-2026-06-27-post2.ts` |
| Stand-in assets | `packages/remotion/public/standin/*.png` |
| Whisper install fix | `packages/remotion/scripts/install-whisper.ts` |
| Run logger | `packages/swarm/content_run_logger.py` |
| Phase 0 pipeline | `packages/swarm/content_pipeline.py` |
| Piece registry | `packages/swarm/content_prompts.py` |
| Tests | `packages/swarm/tests/test_content_pipeline_phase0.py`, `test_content_run_logger.py` |

### CLI

```bash
python -m packages.swarm.content_pipeline --piece reaction-2026-06-27-post2
python -m packages.swarm.content_pipeline --piece reaction-2026-06-27-post2 --dry-run
```

### ReactionDuet layout

- Top 55%: muted source (video or stand-in PNG)
- Bottom 45%: avatar slot (video or stand-in PNG)
- Captions via `Captions.tsx`
- Disclosure badge + single CTA overlay
- Theme from `theme.ts` (MindShift emerald accent for Post #2)
- Duration from WAV via `calculateMetadata`

---

## Kill list (Phase 0 — explicitly NOT built)

- ComfyUI
- GPU VM / cloud lip-sync
- HeyGen avatar
- Postiz scheduling
- Veo / Sora b-roll
- Full 8-step LLM content DAG (Phase 1)

---

## Proof run status

| Step | Expected | Blocker |
|------|----------|---------|
| script | ✅ always | none |
| tts (AZ) | needs `AZURE_SPEECH_KEY` + `AZURE_SPEECH_REGION` | CEO env |
| transcribe | needs TTS output + Node/pnpm | skipped if no WAV |
| render | needs Chromium (Remotion) | skipped if no WAV |
| deliver | needs `TELEGRAM_BOT_TOKEN` + CEO chat id | optional |

Run artifacts land in `memory/swarm/content-runs/{run_id}/`.

---

## CEO-only blockers remaining

1. **Azure Speech keys** — AZ TTS for native accent (Constitution: AZ-first voice)
2. **CEO face clip** — swap stand-in avatar PNG for real lip-sync MP4 when available (Class 49: pipeline works with stand-in now)
3. **Telegram CEO chat id** — set `ATLAS_CEO_CHAT_ID` or `TELEGRAM_CEO_CHAT_ID` for deliver step

---

## Next instance

1. Run dry-run + pytest (should pass without creds)
2. If Azure keys present: full proof run
3. Phase 1: wire LLM script generation + HeyGen + Postiz per `memory/atlas/content-pipeline-handoff.md`
