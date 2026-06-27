/**
 * CLI: render a composition to MP4 / PNG.
 *
 * Usage:
 *   pnpm --filter @volaura/remotion render -- TikTokAZ out/tiktok.mp4
 *   pnpm --filter @volaura/remotion render -- LinkedInCarousel out/carousel.mp4
 *
 * Stitches nicely into the swarm content pipeline:
 *   step 6 (Video Render) calls this script with the composition id and output path.
 */

import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { mkdirSync } from "node:fs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, "..");

function parseArgs(argv: string[]): {
  compositionId: string;
  outPath: string | undefined;
  propsPath: string | undefined;
} {
  const positional = argv.filter((a) => !a.startsWith("--"));
  const flags = Object.fromEntries(
    argv
      .filter((a) => a.startsWith("--"))
      .map((a) => {
        const [k, v] = a.slice(2).split("=");
        return [k, v ?? "true"] as const;
      }),
  );
  const compositionId = positional[0];
  const outPath = positional[1];
  const propsPath = flags.props;
  return { compositionId, outPath, propsPath };
}

async function main() {
  const { compositionId, outPath: outPathArg, propsPath } = parseArgs(
    process.argv.slice(2),
  );

  if (!compositionId) {
    console.error(
      "Usage: render.ts <compositionId> [outputPath] [--props=props.json]",
    );
    process.exit(1);
  }

  let inputProps: Record<string, unknown> | undefined;
  if (propsPath) {
    const raw = await fs.readFile(path.resolve(propsPath), "utf-8");
    inputProps = JSON.parse(raw) as Record<string, unknown>;
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
    inputProps,
  });

  console.log(
    `[remotion] Rendering ${composition.width}x${composition.height} @ ${composition.fps}fps → ${outPath}`,
  );
  await renderMedia({
    composition,
    serveUrl: bundleLocation,
    codec: "h264",
    inputProps,
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
  console.error("[remotion] fatal:", err);
  process.exit(1);
});
