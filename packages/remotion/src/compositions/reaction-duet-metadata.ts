/** Dynamic duration metadata for ReactionDuet — browser-safe (no node:fs). */

import { getAudioDurationInSeconds } from "@remotion/media-utils";
import type { CalculateMetadataFunction } from "remotion";
import { staticFile } from "remotion";
import type { ReactionDuetProps } from "./ReactionDuet";

const FPS = 30;
const DEFAULT_DURATION_SEC = 45;
const CTA_FRAMES = 90;

export const calculateReactionDuetMetadata: CalculateMetadataFunction<
  Record<string, unknown>
> = async ({ props }) => {
  const data = (props as { data?: ReactionDuetProps["data"] }).data;
  const audio = data?.audio;
  if (!audio) {
    return {
      durationInFrames: DEFAULT_DURATION_SEC * FPS,
      fps: FPS,
    };
  }

  try {
    const src = audio.startsWith("http") ? audio : staticFile(audio);
    const durationInSeconds = await getAudioDurationInSeconds(src);
    return {
      durationInFrames: Math.ceil(durationInSeconds * FPS) + CTA_FRAMES,
      fps: FPS,
    };
  } catch {
    return {
      durationInFrames: DEFAULT_DURATION_SEC * FPS,
      fps: FPS,
    };
  }
};
