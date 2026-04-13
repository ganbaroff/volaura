import React from "react";
import {
  AbsoluteFill,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { theme } from "../theme";

// ──────────────────────────────────────────────────────────────
// Slide variants
// ──────────────────────────────────────────────────────────────

export type Slide =
  | { kind: "headline"; eyebrow: string; body: string }
  | { kind: "stat"; value: string; label: string; footnote?: string }
  | { kind: "list"; eyebrow: string; items: string[] }
  | { kind: "quote"; body: string; attribution?: string }
  | { kind: "cta"; headline: string; body: string };

export interface LinkedInCarouselProps {
  data: {
    brand: string;
    title: string;
    subtitle: string;
    slides: Slide[];
  };
}

const SLIDE_FRAMES = 90; // 3s per slide @ 30fps

export const LinkedInCarousel: React.FC<LinkedInCarouselProps> = ({ data }) => {
  return (
    <AbsoluteFill
      style={{
        backgroundColor: theme.color.bg,
        fontFamily: theme.font.sans,
        color: theme.color.text,
      }}
    >
      <Sequence durationInFrames={SLIDE_FRAMES}>
        <CoverSlide title={data.title} subtitle={data.subtitle} brand={data.brand} />
      </Sequence>
      {data.slides.map((slide, i) => (
        <Sequence
          key={i}
          from={(i + 1) * SLIDE_FRAMES}
          durationInFrames={SLIDE_FRAMES}
        >
          <SlideRenderer slide={slide} index={i + 1} brand={data.brand} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

const CoverSlide: React.FC<{ title: string; subtitle: string; brand: string }> = ({
  title,
  subtitle,
  brand,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const appear = spring({ frame, fps, config: { damping: 18 }, durationInFrames: 24 });
  return (
    <SlideShell brand={brand} index={0}>
      <div
        style={{
          opacity: appear,
          transform: `translateY(${(1 - appear) * 20}px)`,
        }}
      >
        <div
          style={{
            fontFamily: theme.font.body,
            fontSize: 28,
            color: theme.color.textMuted,
            marginBottom: 24,
            letterSpacing: 1.2,
            textTransform: "uppercase",
          }}
        >
          {brand} — weekly notes
        </div>
        <h1
          style={{
            fontFamily: theme.font.display,
            fontSize: 88,
            fontWeight: 800,
            lineHeight: 1.05,
            letterSpacing: -1.5,
            marginBottom: 28,
            color: theme.color.text,
          }}
        >
          {title}
        </h1>
        <p
          style={{
            fontFamily: theme.font.body,
            fontSize: 40,
            color: theme.color.textMuted,
            lineHeight: 1.3,
            margin: 0,
          }}
        >
          {subtitle}
        </p>
      </div>
    </SlideShell>
  );
};

const SlideRenderer: React.FC<{ slide: Slide; index: number; brand: string }> = ({
  slide,
  index,
  brand,
}) => {
  if (slide.kind === "headline") {
    return <HeadlineSlide slide={slide} index={index} brand={brand} />;
  }
  if (slide.kind === "stat") {
    return <StatSlide slide={slide} index={index} brand={brand} />;
  }
  if (slide.kind === "list") {
    return <ListSlide slide={slide} index={index} brand={brand} />;
  }
  if (slide.kind === "quote") {
    return <QuoteSlide slide={slide} index={index} brand={brand} />;
  }
  return <CtaSlide slide={slide} index={index} brand={brand} />;
};

const HeadlineSlide: React.FC<{
  slide: Extract<Slide, { kind: "headline" }>;
  index: number;
  brand: string;
}> = ({ slide, index, brand }) => {
  const { appear } = useAppear();
  return (
    <SlideShell brand={brand} index={index}>
      <div style={{ opacity: appear }}>
        <Eyebrow>{slide.eyebrow}</Eyebrow>
        <h2
          style={{
            fontFamily: theme.font.display,
            fontSize: 72,
            fontWeight: 800,
            lineHeight: 1.1,
            letterSpacing: -1.2,
            margin: 0,
          }}
        >
          {slide.body}
        </h2>
      </div>
    </SlideShell>
  );
};

const StatSlide: React.FC<{
  slide: Extract<Slide, { kind: "stat" }>;
  index: number;
  brand: string;
}> = ({ slide, index, brand }) => {
  const frame = useCurrentFrame();
  const { appear } = useAppear();
  // Count-up the stat over 60% of slide length (capped so it feels snappy)
  const numeric = Number(slide.value);
  const isNumber = !Number.isNaN(numeric);
  const n = isNumber
    ? Math.round(
        interpolate(frame, [0, Math.floor(SLIDE_FRAMES * 0.6)], [0, numeric], {
          extrapolateRight: "clamp",
        }),
      )
    : null;

  return (
    <SlideShell brand={brand} index={index}>
      <div style={{ opacity: appear, textAlign: "left" }}>
        <div
          style={{
            fontFamily: theme.font.display,
            fontSize: 340,
            fontWeight: 900,
            lineHeight: 0.95,
            color: theme.color.volaura,
            letterSpacing: -6,
            textShadow: `0 0 60px ${theme.color.volaura}33`,
          }}
        >
          {isNumber ? n : slide.value}
        </div>
        <div
          style={{
            fontFamily: theme.font.body,
            fontSize: 48,
            color: theme.color.text,
            marginTop: 16,
            lineHeight: 1.25,
          }}
        >
          {slide.label}
        </div>
        {slide.footnote && (
          <div
            style={{
              fontFamily: theme.font.body,
              fontSize: 28,
              color: theme.color.textMuted,
              marginTop: 24,
              lineHeight: 1.35,
              maxWidth: 900,
            }}
          >
            {slide.footnote}
          </div>
        )}
      </div>
    </SlideShell>
  );
};

const ListSlide: React.FC<{
  slide: Extract<Slide, { kind: "list" }>;
  index: number;
  brand: string;
}> = ({ slide, index, brand }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <SlideShell brand={brand} index={index}>
      <div>
        <Eyebrow>{slide.eyebrow}</Eyebrow>
        <ul
          style={{
            listStyle: "none",
            padding: 0,
            margin: 0,
            display: "flex",
            flexDirection: "column",
            gap: 20,
          }}
        >
          {slide.items.map((item, i) => {
            const enter = spring({
              frame: frame - 8 - i * 10,
              fps,
              config: { damping: 18 },
              durationInFrames: 20,
            });
            return (
              <li
                key={i}
                style={{
                  fontFamily: theme.font.body,
                  fontSize: 44,
                  lineHeight: 1.3,
                  opacity: enter,
                  transform: `translateX(${(1 - enter) * 24}px)`,
                  display: "flex",
                  gap: 24,
                }}
              >
                <span style={{ color: theme.color.volaura, fontWeight: 800 }}>·</span>
                <span>{item}</span>
              </li>
            );
          })}
        </ul>
      </div>
    </SlideShell>
  );
};

const QuoteSlide: React.FC<{
  slide: Extract<Slide, { kind: "quote" }>;
  index: number;
  brand: string;
}> = ({ slide, index, brand }) => {
  const { appear } = useAppear();
  return (
    <SlideShell brand={brand} index={index}>
      <div style={{ opacity: appear, maxWidth: 920 }}>
        <div
          style={{
            fontFamily: theme.font.display,
            fontSize: 56,
            fontStyle: "italic",
            fontWeight: 600,
            lineHeight: 1.2,
            color: theme.color.text,
          }}
        >
          “{slide.body}”
        </div>
        {slide.attribution && (
          <div
            style={{
              fontFamily: theme.font.body,
              fontSize: 28,
              color: theme.color.textMuted,
              marginTop: 32,
            }}
          >
            {slide.attribution}
          </div>
        )}
      </div>
    </SlideShell>
  );
};

const CtaSlide: React.FC<{
  slide: Extract<Slide, { kind: "cta" }>;
  index: number;
  brand: string;
}> = ({ slide, index, brand }) => {
  const { appear } = useAppear();
  return (
    <SlideShell brand={brand} index={index}>
      <div style={{ opacity: appear }}>
        <h2
          style={{
            fontFamily: theme.font.display,
            fontSize: 88,
            fontWeight: 800,
            color: theme.color.volaura,
            letterSpacing: -1.5,
            lineHeight: 1.05,
            margin: 0,
          }}
        >
          {slide.headline}
        </h2>
        <p
          style={{
            fontFamily: theme.font.body,
            fontSize: 40,
            color: theme.color.textMuted,
            marginTop: 28,
            maxWidth: 880,
            lineHeight: 1.3,
          }}
        >
          {slide.body}
        </p>
      </div>
    </SlideShell>
  );
};

// ──────────────────────────────────────────────────────────────
// Shell + helpers
// ──────────────────────────────────────────────────────────────

const SlideShell: React.FC<
  React.PropsWithChildren<{ brand: string; index: number }>
> = ({ children, brand, index }) => {
  return (
    <AbsoluteFill
      style={{
        padding: 96,
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
      }}
    >
      <div style={{ flex: 1, display: "flex", alignItems: "center" }}>{children}</div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontFamily: theme.font.body,
          fontSize: 24,
          color: theme.color.textDim,
          letterSpacing: 1.2,
          textTransform: "uppercase",
        }}
      >
        <span>{brand}</span>
        <span>{String(index).padStart(2, "0")} / 08</span>
      </div>
    </AbsoluteFill>
  );
};

const Eyebrow: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div
    style={{
      fontFamily: theme.font.body,
      fontSize: 26,
      color: theme.color.volaura,
      letterSpacing: 1.6,
      textTransform: "uppercase",
      marginBottom: 28,
      fontWeight: 700,
    }}
  >
    {children}
  </div>
);

function useAppear() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const appear = spring({ frame, fps, config: { damping: 18 }, durationInFrames: 20 });
  return { appear };
}
