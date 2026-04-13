/**
 * CLI: render a composition to MP4 / PNG.
 *
 * Usage:
 *   pnpm --filter @volaura/remotion render -- TikTokAZ out/tiktok.mp4
 *   pnpm --filter @volaura/remotion render -- LinkedInCarousel out/carousel.mp4
 *
 * Stitches nicely into the swarm content pipeline:
 *   step 7 (Video Render) calls this script with the composition id and output path.
 */

import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { mkdirSync } from "node:fs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, "..");

async function main() {
  const [, , compositionId, outPathArg] = process.argv;

  if (!compositionId) {
    console.error("Usage: render.ts <compositionId> [outputPath]");
    process.exit(1);
  }

  const outPath = outPathArg
    ? path.resolve(process.cwd(), outPathArg)
    : path.resolve(ROOT, "out", `${compositionId}-${Date.now()}.mp4`);

  mkdirSync(path.dirname(outPath), { recursive: true });

  console.log(`[remotion] Bundling ${ROOT}/src/index.tsx …`);
  const bundleLocation = await bundle({
    entryPoint: path.resolve(ROOT, "src/index.tsx"),
    webpackOverride: (config) => config,
  });

  console.log(`[remotion] Selecting composition "${compositionId}" …`);
  const composition = await selectComposition({
    serveUrl: bundleLocation,
    id: compositionId,
  });

  console.log(
    `[remotion] Rendering ${composition.width}x${composition.height} @ ${composition.fps}fps → ${outPath}`,
  );
  await renderMedia({
    composition,
    serveUrl: bundleLocation,
    codec: "h264",
    outputLocation: outPath,
    onProgress: ({ progress }) => {
      const pct = Math.round(progress * 100);
      process.stdout.write(`\r[remotion] progress: ${pct}%  `);
    },
  });

  process.stdout.write("\n");
  console.log(`[remotion] ✓ done → ${outPath}`);
}

main().catch((err) => {
  console.error("[remotion] render failed:", err);
  process.exit(1);
});
