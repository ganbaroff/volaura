import React from "react";
import {
  AbsoluteFill,
  Audio,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  staticFile,
} from "remotion";
import type { Caption } from "@remotion/captions";
import { theme } from "../theme";
import { Captions } from "../components/Captions";

// ──────────────────────────────────────────────────────────────
// Props (data is typed so content pipeline can fill it safely)
// ──────────────────────────────────────────────────────────────

type Beat =
  | {
      kind: "statement";
      text: string;
      highlight: string;
    }
  | {
      kind: "contrast";
      text: string;
      highlight: string;
      textTail: string;
    }
  | {
      kind: "counter";
      label: string;
      from: number;
      to: number;
      suffix?: string;
    }
  | {
      kind: "punchline";
      text: string;
      highlight: string;
    };

export interface TikTokAZProps {
  data: {
    brandHandle: string;
    accentProduct: "volaura" | "mindshift" | "lifeSim" | "brandedBy" | "atlas";
    hook: { line1: string; line2: string };
    beats: Beat[];
    cta: { line: string; brand: string };
    agentNames: string[];
    /** Optional voice-over track. Relative to `public/` for `staticFile()` or absolute URL. */
    audio?: string;
    /** Optional word-level captions (from scripts/transcribe.ts). */
    captions?: Caption[];
  };
}

// ──────────────────────────────────────────────────────────────
// Timing plan (30 fps, 45s total = 1350 frames)
// ──────────────────────────────────────────────────────────────
//  Hook        0 →  90f   (0–3s)
//  Beat 1     90 → 180f   (3–6s)
//  Beat 2    180 → 270f   (6–9s)
//  Audit     270 → 750f   (9–25s) — agent name scroll
//  Counter   750 → 960f   (25–32s)
//  Punchline 960 → 1200f  (32–40s)
//  CTA      1200 → 1350f  (40–45s)
// ──────────────────────────────────────────────────────────────

const FPS = 30;
const seg = {
  hook: { from: 0, durationInFrames: 90 },
  beat1: { from: 90, durationInFrames: 90 },
  beat2: { from: 180, durationInFrames: 90 },
  audit: { from: 270, durationInFrames: 480 },
  counter: { from: 750, durationInFrames: 210 },
  punchline: { from: 960, durationInFrames: 240 },
  cta: { from: 1200, durationInFrames: 150 },
};

// ──────────────────────────────────────────────────────────────
// Root composition
// ──────────────────────────────────────────────────────────────

export const TikTokAZ: React.FC<TikTokAZProps> = ({ data }) => {
  const accent = theme.color[data.accentProduct] ?? theme.color.volaura;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: theme.color.bg,
        fontFamily: theme.font.sans,
        color: theme.color.text,
        overflow: "hidden",
      }}
    >
      <BackgroundGlow accent={accent} />
      <NoiseOverlay />

      <Sequence {...seg.hook}>
        <Hook line1={data.hook.line1} line2={data.hook.line2} accent={accent} />
      </Sequence>

      <Sequence {...seg.beat1}>
        {data.beats[0] && <BeatRenderer beat={data.beats[0]} accent={accent} />}
      </Sequence>

      <Sequence {...seg.beat2}>
        {data.beats[1] && <BeatRenderer beat={data.beats[1]} accent={accent} />}
      </Sequence>

      <Sequence {...seg.audit}>
        <AgentScroll names={data.agentNames} accent={accent} />
      </Sequence>

      <Sequence {...seg.counter}>
        {data.beats[2]?.kind === "counter" && (
          <CounterScene beat={data.beats[2]} accent={accent} />
        )}
      </Sequence>

      <Sequence {...seg.punchline}>
        {data.beats[3] && <BeatRenderer beat={data.beats[3]} accent={accent} />}
      </Sequence>

      <Sequence {...seg.cta}>
        <CTA cta={data.cta} handle={data.brandHandle} accent={accent} />
      </Sequence>

      {data.audio ? (
        <Audio
          src={
            data.audio.startsWith("http") || data.audio.startsWith("/")
              ? data.audio
              : staticFile(data.audio)
          }
        />
      ) : null}

      {data.captions && data.captions.length > 0 ? (
        <Captions captions={data.captions} accentColor={accent} />
      ) : null}
    </AbsoluteFill>
  );
};

// ──────────────────────────────────────────────────────────────
// Scenes
// ──────────────────────────────────────────────────────────────

const Hook: React.FC<{ line1: string; line2: string; accent: string }> = ({
  line1,
  line2,
  accent,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Line 1 enters at 0, line 2 at 20f (~0.67s). Max 800ms per spring.
  const s1 = spring({ frame, fps, config: { damping: 16 }, durationInFrames: 20 });
  const s2 = spring({
    frame: frame - 20,
    fps,
    config: { damping: 16 },
    durationInFrames: 20,
  });

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 80,
        textAlign: "left",
      }}
    >
      <div style={{ maxWidth: 880 }}>
        <div
          style={{
            fontFamily: theme.font.display,
            fontSize: 140,
            fontWeight: 800,
            lineHeight: 1.02,
            letterSpacing: -2,
            opacity: s1,
            transform: `translateY(${(1 - s1) * 24}px)`,
          }}
        >
          {line1}
        </div>
        <div
          style={{
            fontFamily: theme.font.display,
            fontSize: 140,
            fontWeight: 800,
            lineHeight: 1.02,
            letterSpacing: -2,
            color: accent,
            opacity: s2,
            transform: `translateY(${(1 - s2) * 24}px)`,
          }}
        >
          {line2}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const BeatRenderer: React.FC<{ beat: Beat; accent: string }> = ({ beat, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const appear = spring({ frame, fps, config: { damping: 16 }, durationInFrames: 20 });

  const containerStyle: React.CSSProperties = {
    padding: 80,
    textAlign: "left",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  };

  const textStyle: React.CSSProperties = {
    fontFamily: theme.font.display,
    fontSize: 118,
    fontWeight: 800,
    lineHeight: 1.05,
    letterSpacing: -1.5,
    opacity: appear,
    transform: `translateY(${(1 - appear) * 16}px)`,
    maxWidth: 880,
  };

  if (beat.kind === "statement") {
    return (
      <AbsoluteFill style={containerStyle}>
        <div style={textStyle}>
          {beat.text}
          <div style={{ color: accent, marginTop: 12 }}>{beat.highlight}</div>
        </div>
      </AbsoluteFill>
    );
  }

  if (beat.kind === "contrast") {
    return (
      <AbsoluteFill style={containerStyle}>
        <div style={textStyle}>
          {beat.text}{" "}
          <span
            style={{
              display: "inline-block",
              color: accent,
              fontSize: 220,
              lineHeight: 1,
              verticalAlign: "middle",
            }}
          >
            {beat.highlight}
          </span>{" "}
          {beat.textTail}
        </div>
      </AbsoluteFill>
    );
  }

  if (beat.kind === "punchline") {
    return (
      <AbsoluteFill style={containerStyle}>
        <div style={textStyle}>
          <div style={{ color: theme.color.textMuted, fontSize: 92 }}>{beat.text}</div>
          <div style={{ color: accent, marginTop: 16 }}>{beat.highlight}</div>
        </div>
      </AbsoluteFill>
    );
  }

  // counter variant handled by CounterScene
  return null;
};

const CounterScene: React.FC<{
  beat: Extract<Beat, { kind: "counter" }>;
  accent: string;
}> = ({ beat, accent }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // Counter ramps up over 60% of the segment, rests for 40%
  const rampFrames = Math.floor(seg.counter.durationInFrames * 0.6);
  const n = Math.round(
    interpolate(frame, [0, rampFrames], [beat.from, beat.to], {
      extrapolateRight: "clamp",
    }),
  );

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: 80,
      }}
    >
      <div
        style={{
          fontFamily: theme.font.body,
          fontSize: 40,
          color: theme.color.textMuted,
          marginBottom: 32,
          textAlign: "center",
        }}
      >
        {beat.label}
      </div>
      <div
        style={{
          fontFamily: theme.font.display,
          fontSize: 440,
          fontWeight: 900,
          color: accent,
          lineHeight: 1,
          textShadow: `0 0 80px ${accent}40`,
        }}
      >
        {n}
      </div>
      {beat.suffix && (
        <div
          style={{
            fontFamily: theme.font.body,
            fontSize: 48,
            color: theme.color.text,
            marginTop: 16,
          }}
        >
          {beat.suffix}
        </div>
      )}
    </AbsoluteFill>
  );
};

const AgentScroll: React.FC<{ names: string[]; accent: string }> = ({ names, accent }) => {
  const frame = useCurrentFrame();
  // Scroll from bottom to top over the whole audit segment
  const progress = interpolate(
    frame,
    [0, seg.audit.durationInFrames],
    [0, 1],
    { extrapolateRight: "clamp" },
  );
  const totalHeight = names.length * 160;

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 60,
        overflow: "hidden",
      }}
    >
      <div
        style={{
          transform: `translateY(${(1 - progress) * totalHeight * 0.4}px)`,
          display: "flex",
          flexDirection: "column",
          gap: 32,
          width: "100%",
        }}
      >
        {names.map((name, i) => (
          <AgentRow key={name} name={name} index={i} accent={accent} />
        ))}
      </div>
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 240,
          background: `linear-gradient(${theme.color.bg}, transparent)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: 240,
          background: `linear-gradient(transparent, ${theme.color.bg})`,
        }}
      />
    </AbsoluteFill>
  );
};

const AgentRow: React.FC<{ name: string; index: number; accent: string }> = ({
  name,
  index,
  accent,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  // Each agent "checks" ~every 30 frames. Green check flashes.
  const checkFrame = index * 32;
  const checkProgress = spring({
    frame: frame - checkFrame,
    fps,
    config: { damping: 18 },
    durationInFrames: 20,
  });
  const showCheck = frame >= checkFrame;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "24px 48px",
        backgroundColor: theme.color.bgElevated,
        border: `2px solid ${showCheck ? accent + "40" : "#ffffff10"}`,
        borderRadius: 24,
        fontFamily: theme.font.body,
        fontSize: 44,
        fontWeight: 600,
      }}
    >
      <span>{name}</span>
      <span
        style={{
          color: accent,
          fontSize: 56,
          opacity: showCheck ? checkProgress : 0,
          transform: `scale(${showCheck ? 0.8 + checkProgress * 0.2 : 0.8})`,
        }}
      >
        ✓
      </span>
    </div>
  );
};

const CTA: React.FC<{
  cta: TikTokAZProps["data"]["cta"];
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
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 80,
      }}
    >
      <div
        style={{
          opacity: appear,
          transform: `translateY(${(1 - appear) * 20}px)`,
          textAlign: "center",
        }}
      >
        <div
          style={{
            fontFamily: theme.font.body,
            fontSize: 48,
            color: theme.color.textMuted,
            marginBottom: 24,
          }}
        >
          {cta.line}
        </div>
        <div
          style={{
            fontFamily: theme.font.display,
            fontSize: 128,
            fontWeight: 800,
            color: accent,
            letterSpacing: -1.5,
          }}
        >
          {cta.brand}
        </div>
        <div
          style={{
            fontFamily: theme.font.body,
            fontSize: 36,
            color: theme.color.textDim,
            marginTop: 40,
          }}
        >
          {handle}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ──────────────────────────────────────────────────────────────
// Decorations
// ──────────────────────────────────────────────────────────────

const BackgroundGlow: React.FC<{ accent: string }> = ({ accent }) => {
  const frame = useCurrentFrame();
  // Slow ambient drift (decorative — per Law 4 it's allowed because it's not driving attention)
  const t = frame / 1350;
  const x = Math.sin(t * Math.PI * 2) * 120;
  const y = Math.cos(t * Math.PI * 2) * 80;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          width: 900,
          height: 900,
          borderRadius: "50%",
          background: `radial-gradient(circle, ${accent}33 0%, transparent 70%)`,
          left: `calc(50% - 450px + ${x}px)`,
          top: `calc(30% - 450px + ${y}px)`,
          filter: "blur(40px)",
        }}
      />
    </AbsoluteFill>
  );
};

const NoiseOverlay: React.FC = () => (
  <AbsoluteFill
    style={{
      pointerEvents: "none",
      opacity: 0.04,
      mixBlendMode: "overlay",
      backgroundImage:
        "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>\")",
      backgroundSize: "200px 200px",
    }}
  />
);