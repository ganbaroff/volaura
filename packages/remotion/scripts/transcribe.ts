#!/usr/bin/env tsx
/**
 * transcribe.ts — Generate word-level captions for a voice-over audio file.
 *
 * Usage:
 *   pnpm --filter @volaura/remotion transcribe <audio.wav> [--model=large-v3-turbo] [--language=az]
 *
 * Output:
 *   <audio-basename>.captions.json — Caption[] consumable by <Captions /> component.
 *
 * Constitution:
 *   - Runs locally. No cloud API. No data leaves Atlas's machine.
 *   - Supports AZ natively (whisper.cpp ggml-large-v3-turbo includes Azerbaijani).
 *   - Deterministic: same audio + same model = same captions (cacheable).
 */
import fs from "node:fs/promises";
import path from "node:path";
import {
  installWhisperCpp,
  transcribe,
  toCaptions,
  downloadWhisperModel,
  type WhisperModel,
} from "@remotion/install-whisper-cpp";

const WHISPER_PATH = path.resolve(process.cwd(), ".whisper");
const WHISPER_VERSION = "1.7.1";
const DEFAULT_MODEL: WhisperModel = "large-v3-turbo";

type ParsedArgs = {
  audioPath: string;
  model: WhisperModel;
  language: string | null;
  outPath: string;
};

function parseArgs(argv: string[]): ParsedArgs {
  const positional = argv.filter((a) => !a.startsWith("--"));
  if (positional.length === 0) {
    throw new Error(
      "Usage: transcribe.ts <audio.wav> [--model=large-v3-turbo] [--language=az]",
    );
  }
  const audioPath = path.resolve(positional[0]);
  const flags = Object.fromEntries(
    argv
      .filter((a) => a.startsWith("--"))
      .map((a) => {
        const [k, v] = a.slice(2).split("=");
        return [k, v ?? "true"] as const;
      }),
  );
  const model = (flags.model ?? DEFAULT_MODEL) as WhisperModel;
  const language =
    flags.language && flags.language !== "auto" ? flags.language : null;
  const outPath =
    flags.out ??
    path.join(
      path.dirname(audioPath),
      path.basename(audioPath, path.extname(audioPath)) + ".captions.json",
    );
  return { audioPath, model, language, outPath };
}

async function main() {
  const { audioPath, model, language, outPath } = parseArgs(
    process.argv.slice(2),
  );

  await fs.mkdir(WHISPER_PATH, { recursive: true });

  console.log(`[captions] whisper.cpp @ ${WHISPER_VERSION} → ${WHISPER_PATH}`);
  const { alreadyExisted: binExisted } = await installWhisperCpp({
    version: WHISPER_VERSION,
    to: WHISPER_PATH,
    printOutput: false,
  });
  console.log(
    `[captions] whisper binary ${binExisted ? "already installed" : "installed"}`,
  );

  console.log(`[captions] model ${model} → ${WHISPER_PATH}/models`);
  const { alreadyExisted: modelExisted } = await downloadWhisperModel({
    model,
    folder: WHISPER_PATH,
    printOutput: false,
  });
  console.log(
    `[captions] model ${modelExisted ? "cached" : "downloaded"} (${model})`,
  );

  console.log(
    `[captions] transcribing ${audioPath}${language ? ` [lang=${language}]` : " [auto-detect]"}`,
  );
  const result = await transcribe({
    inputPath: audioPath,
    whisperPath: WHISPER_PATH,
    whisperCppVersion: WHISPER_VERSION,
    model,
    tokenLevelTimestamps: true,
    language: (language as never) ?? undefined,
    splitOnWord: true,
    printOutput: false,
  });

  const { captions } = toCaptions({ whisperCppOutput: result });
  await fs.writeFile(outPath, JSON.stringify(captions, null, 2), "utf-8");

  console.log(
    `[captions] done → ${outPath} (${captions.length} tokens, detected lang=${result.result.language})`,
  );
}

main().catch((err) => {
  console.error("[captions] fatal:", err);
  process.exit(1);
});
