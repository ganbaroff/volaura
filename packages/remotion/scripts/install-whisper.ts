#!/usr/bin/env tsx
/**
 * install-whisper.ts — Pre-install whisper.cpp binary + default model.
 *
 * Alias target for `pnpm install-whisper`. The full transcribe script also
 * installs on first run; this script lets the content pipeline warm caches
 * without needing an audio file.
 */
import fs from "node:fs/promises";
import path from "node:path";
import {
  installWhisperCpp,
  downloadWhisperModel,
  type WhisperModel,
} from "@remotion/install-whisper-cpp";

const WHISPER_PATH = path.resolve(process.cwd(), ".whisper");
const WHISPER_VERSION = "1.7.1";
const DEFAULT_MODEL: WhisperModel = "large-v3-turbo";

async function main() {
  const modelArg = process.argv.find((a) => a.startsWith("--model="));
  const model = (modelArg?.split("=")[1] ?? DEFAULT_MODEL) as WhisperModel;

  await fs.mkdir(WHISPER_PATH, { recursive: true });

  console.log(`[whisper] installing binary @ ${WHISPER_VERSION} → ${WHISPER_PATH}`);
  const { alreadyExisted: binExisted } = await installWhisperCpp({
    version: WHISPER_VERSION,
    to: WHISPER_PATH,
    printOutput: false,
  });
  console.log(
    `[whisper] binary ${binExisted ? "already present" : "installed"}`,
  );

  console.log(`[whisper] downloading model ${model}`);
  const { alreadyExisted: modelExisted } = await downloadWhisperModel({
    model,
    folder: WHISPER_PATH,
    printOutput: false,
  });
  console.log(
    `[whisper] model ${modelExisted ? "cached" : "downloaded"} (${model})`,
  );
  console.log("[whisper] ready");
}

main().catch((err) => {
  console.error("[whisper] fatal:", err);
  process.exit(1);
});
