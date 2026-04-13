import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import {
  createTikTokStyleCaptions,
  type Caption,
  type TikTokPage,
  type TikTokToken,
} from "@remotion/captions";
import { theme } from "../theme";

/**
 * Captions.tsx — TikTok-style word-by-word caption overlay.
 *
 * Data flow (Constitution v1.7 § Foundation Law 4 — animation safety):
 *   1. `scripts/transcribe.ts` runs whisper.cpp on the voice-over audio
 *      → produces `data/<slug>.captions.json` (Caption[]).
 *   2. This component consumes Caption[] → createTikTokStyleCaptions()
 *      → per-page, per-token reveals with < 800ms spring pops.
 *   3. Active token pops in with spring(damping=16), inactive tokens are
 *      dim at 55% opacity — no red, no flash, ADHD-safe.
 *
 * Safety rails:
 *   - `maxCombineMs` (default 1500) bounds how many words share a page.
 *   - Active token scale is capped at 1.08× to avoid motion-sickness spikes.
 *   - Respects prefers-reduced-motion by disabling the pop (constant scale 1).
 */
export type CaptionsProps = {
  captions: Caption[];
  /** Maximum ms a single page can span. Default 1500ms (~3-5 short AZ words). */
  maxCombineMs?: number;
  /** Position from bottom in % of frame height. Default 18 (safe above TikTok UI). */
  bottomInsetPercent?: number;
  /** Override accent color for the active word. Defaults to VOLAURA indigo. */
  accentColor?: string;
  /** Disable the spring pop when user has prefers-reduced-motion. Default true. */
  respectReducedMotion?: boolean;
};

export const Captions: React.FC<CaptionsProps> = ({
  captions,
  maxCombineMs = 1500,
  bottomInsetPercent = 18,
  accentColor = theme.color.volaura,
  respectReducedMotion = true,
}) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const nowMs = (frame / fps) * 1000;

  const { pages } = React.useMemo(
    () =>
      createTikTokStyleCaptions({
        captions,
        combineTokensWithinMilliseconds: maxCombineMs,
      }),
    [captions, maxCombineMs],
  );

  const activePage = React.useMemo(
    () =>
      pages.find(
        (p: TikTokPage) =>
          nowMs >= p.startMs && nowMs < p.startMs + p.durationMs,
      ),
    [pages, nowMs],
  );

  if (!activePage) {
    return null;
  }

  const reducedMotion =
    respectReducedMotion &&
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: `${bottomInsetPercent}%`,
        paddingLeft: 56,
        paddingRight: 56,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          alignItems: "baseline",
          gap: 14,
          fontFamily: theme.font.display,
          fontWeight: 800,
          fontSize: Math.round(height * 0.042), // ~80px at 1920 tall
          lineHeight: 1.08,
          letterSpacing: "-0.02em",
          color: theme.color.text,
          textAlign: "center",
          textShadow: "0 2px 18px rgba(0,0,0,0.55)",
        }}
      >
        {activePage.tokens.map((token: TikTokToken, idx: number) => {
          const isActive = nowMs >= token.fromMs && nowMs < token.toMs;
          const tokenFrame = frame - (token.fromMs / 1000) * fps;
          const pop = reducedMotion
            ? 1
            : spring({
                frame: Math.max(0, tokenFrame),
                fps,
                config: { damping: 16, stiffness: 240, mass: 0.6 },
              });
          const scale = isActive
            ? interpolate(pop, [0, 1], [0.88, 1.08], {
                extrapolateRight: "clamp",
              })
            : 1;
          const opacity = isActive ? 1 : 0.55;
          return (
            <span
              key={`${activePage.startMs}-${idx}`}
              style={{
                display: "inline-block",
                transform: `scale(${scale})`,
                transformOrigin: "center center",
                opacity,
                color: isActive ? accentColor : theme.color.text,
                transition: "color 80ms linear",
                willChange: "transform, opacity",
              }}
            >
              {token.text}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
