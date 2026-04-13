# @volaura/remotion

Video rendering for VOLAURA ecosystem weekly content batches.
Turns typed content data (`src/data/*.ts`) into real MP4 / PNG output via Remotion.

## Why

Until now, the weekly content batch (`docs/content/weekly-plans/*.md` + the 6-step content pipeline in `memory/atlas/content-pipeline-handoff.md`) ended at **text**: scripts, captions, carousel outlines. CEO directive 2026-04-13: "нужно чтобы был и сам контент, а не только промпты." This package is **Step 7 — Video Render** of that pipeline.

## Compositions

| id | format | size | duration | source data |
|---|---|---|---|---|
| `TikTokAZ` | vertical MP4 | 1080×1920 | 45 s | `src/data/tiktok-2026-04-13.ts` |
| `LinkedInCarousel` | portrait MP4 / PNG frames | 1080×1350 | 24 s (8 slides × 3 s) | `src/data/carousel-2026-04-13.ts` |

New weekly batch → add a new `src/data/*.ts` file with typed content and register a new `<Composition>` (or reuse an existing one) in `src/Root.tsx`.

## Design tokens

All compositions consume `src/theme.ts`, which mirrors `apps/web/app/globals.css`. Constitution v1.7 compliant: NEVER RED (errors/alerts in purple `#D4B4FF`, warnings amber `#E9C400`), max 800 ms non-decorative animation, one primary CTA per frame.

## Install

```bash
# From repo root
pnpm install
# Or just this package
pnpm --filter @volaura/remotion install
```

Requires Node 20+ and Chromium (Remotion downloads its own on first run).

## Usage

### Interactive preview

```bash
pnpm --filter @volaura/remotion studio
```

Opens Remotion Studio at `http://localhost:3000`.

### One-shot render

```bash
pnpm --filter @volaura/remotion render -- TikTokAZ out/tiktok-2026-04-13.mp4
pnpm --filter @volaura/remotion render -- LinkedInCarousel out/carousel-2026-04-13.mp4
```

### Export individual carousel slides as PNG (for LinkedIn PDF upload)

```bash
pnpm --filter @volaura/remotion exec remotion still LinkedInCarousel out/slide-%03d.png
```

## Pipeline integration

Add to `packages/swarm/content_pipeline.py` as Step 7:

```python
# Step 7 — Video Render (new)
if piece.format in {"tiktok_az", "linkedin_carousel"}:
    comp_id = "TikTokAZ" if piece.format == "tiktok_az" else "LinkedInCarousel"
    out = f"out/{piece.slug}.mp4"
    subprocess.run(
        ["pnpm", "--filter", "@volaura/remotion", "render", "--", comp_id, out],
        check=True,
    )
    piece.media_path = out
```

Telegram Ambassador (Step 6) attaches `piece.media_path` as a file instead of text when present.

## Adding a new composition

1. Create `src/data/my-piece.ts` exporting typed props.
2. Create `src/compositions/MyPiece.tsx` — a React component.
3. Register in `src/Root.tsx`.
4. Add `render:my-piece` script to `package.json` if the batch needs a stable command.

## Constitution check

Before rendering any new composition:

```bash
pnpm --filter @volaura/remotion typecheck
pnpm --filter @volaura/remotion lint
python -m packages.swarm.tools.constitution_checker --only-live
```

All three must pass. The `constitution_checker` rule set currently flags source under `packages/remotion/` same as `apps/web/`.

## Troubleshooting

- **`Failed to launch Chromium`** — run `pnpm --filter @volaura/remotion exec npx @remotion/cli browser` to install a compatible Chromium for the host.
- **Fonts missing** — Remotion ships with Plus Jakarta Sans + Inter via `@remotion/google-fonts`. If they don't load, check network access from the renderer.
- **Rendering is slow** — Remotion uses all cores by default. Reduce `Config.setConcurrency(4)` in `remotion.config.ts` if the machine is memory-constrained.
