import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  OffthreadVideo,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { Caption } from "@remotion/captions";
import { theme, type ThemeProductKey } from "../theme";
import { Captions } from "../components/Captions";

// ──────────────────────────────────────────────────────────────
// Props
// ──────────────────────────────────────────────────────────────

export interface ReactionDuetProps {
  data: {
    brandHandle: string;
    accentProduct: ThemeProductKey;
    /** Muted source clip — relative to `public/` or absolute URL. */
    sourceVideo?: string;
    /** Static stand-in when no source video yet (Class 49). */
    sourceImage?: string;
    /** Avatar video in bottom slot. */
    avatarVideo?: string;
    /** Static avatar placeholder when no lip-sync clip yet. */
    avatarImage?: string;
    audio?: string;
    captions?: Caption[];
    disclosure: string;
    cta: { line: string; brand: string };
  };
}

const CTA_FRAMES = 90;

function resolveMediaSrc(src: string): string {
  if (src.startsWith("http") || src.startsWith("/")) {
    return src;
  }
  return staticFile(src);
}

// ──────────────────────────────────────────────────────────────
// Root composition — reaction/duet layout
// Top 55%: muted source | Bottom 45%: avatar | Captions overlay
// ──────────────────────────────────────────────────────────────

export const ReactionDuet: React.FC<ReactionDuetProps> = ({ data }) => {
  const accent = theme.color[data.accentProduct] ?? theme.color.volaura;
  const { durationInFrames } = useVideoConfig();
  const ctaFrom = Math.max(0, durationInFrames - CTA_FRAMES);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: theme.color.bg,
        fontFamily: theme.font.sans,
        color: theme.color.text,
        overflow: "hidden",
      }}
    >
      {/* Top 55% — muted source */}
      <AbsoluteFill
        style={{
          top: 0,
          height: "55%",
          overflow: "hidden",
          borderBottom: `3px solid ${accent}33`,
        }}
      >
        {data.sourceVideo ? (
          <OffthreadVideo
            src={resolveMediaSrc(data.sourceVideo)}
            muted
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        ) : (
          <Img
            src={resolveMediaSrc(
              data.sourceImage ?? "standin/source-placeholder.png",
            )}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        )}
        <DisclosureBadge text={data.disclosure} accent={accent} />
      </AbsoluteFill>

      {/* Bottom 45% — avatar slot */}
      <AbsoluteFill
        style={{
          top: "55%",
          height: "45%",
          overflow: "hidden",
          backgroundColor: theme.color.bgElevated,
        }}
      >
        {data.avatarVideo ? (
          <OffthreadVideo
            src={resolveMediaSrc(data.avatarVideo)}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        ) : (
          <Img
            src={resolveMediaSrc(
              data.avatarImage ?? "standin/avatar-placeholder.png",
            )}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        )}
      </AbsoluteFill>

      {data.audio ? (
        <Audio src={resolveMediaSrc(data.audio)} />
      ) : null}

      {data.captions && data.captions.length > 0 ? (
        <Captions
          captions={data.captions}
          accentColor={accent}
          bottomInsetPercent={22}
        />
      ) : null}

      <Sequence from={ctaFrom} durationInFrames={CTA_FRAMES}>
        <CTAOverlay
          cta={data.cta}
          handle={data.brandHandle}
          accent={accent}
        />
      </Sequence>
    </AbsoluteFill>
  );
};

// ──────────────────────────────────────────────────────────────
// UI chrome
// ──────────────────────────────────────────────────────────────

const DisclosureBadge: React.FC<{ text: string; accent: string }> = ({
  text,
  accent,
}) => (
  <div
    style={{
      position: "absolute",
      top: 32,
      left: 32,
      padding: "12px 20px",
      borderRadius: theme.radius.pill,
      backgroundColor: theme.color.bgGlass,
      border: `2px solid ${accent}55`,
      fontFamily: theme.font.body,
      fontSize: 28,
      fontWeight: 600,
      color: theme.color.textMuted,
      backdropFilter: "blur(8px)",
    }}
  >
    {text}
  </div>
);

const CTAOverlay: React.FC<{
  cta: ReactionDuetProps["data"]["cta"];
  handle: string;
  accent: string;
}> = ({ cta, handle, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const appear = spring({
    frame,
    fps,
    config: { damping: 16 },
    durationInFrames: 24,
  });

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: 48,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          opacity: appear,
          transform: `translateY(${(1 - appear) * 16}px)`,
          textAlign: "center",
          padding: "28px 48px",
          borderRadius: theme.radius.lg,
          backgroundColor: theme.color.bgGlass,
          border: `2px solid ${accent}66`,
        }}
      >
        <div
          style={{
            fontFamily: theme.font.body,
            fontSize: 36,
            color: theme.color.textMuted,
            marginBottom: 12,
          }}
        >
          {cta.line}
        </div>
        <div
          style={{
            fontFamily: theme.font.display,
            fontSize: 72,
            fontWeight: 800,
            color: accent,
            letterSpacing: -1,
          }}
        >
          {cta.brand}
        </div>
        <div
          style={{
            fontFamily: theme.font.body,
            fontSize: 28,
            color: theme.color.textDim,
            marginTop: 16,
          }}
        >
          {handle}
        </div>
      </div>
    </AbsoluteFill>
  );
};
