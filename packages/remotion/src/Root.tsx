import React from "react";
import { Composition } from "remotion";
import { TikTokAZ } from "./compositions/TikTokAZ";
import { LinkedInCarousel } from "./compositions/LinkedInCarousel";
import { tiktokAZ20260413Post2 } from "./data/tiktok-2026-04-13";
import { carouselData20260413 } from "./data/carousel-2026-04-13";
import { theme } from "./theme";

/**
 * Composition registry.
 * Each composition = one video format. Data is injected via defaultProps.
 * New weekly batches → add new data file + register a new Composition (or reuse an existing one with new data).
 *
 * Note: Remotion's <Composition> requires Props extend Record<string, unknown>.
 * Our compositions declare domain-specific interfaces (TikTokAZProps, etc.), which
 * are structurally compatible but not assignable without a widening cast.
 */
export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="TikTokAZ"
        component={TikTokAZ as unknown as React.FC<Record<string, unknown>>}
        durationInFrames={45 * 30}
        fps={30}
        width={theme.size.tiktok.width}
        height={theme.size.tiktok.height}
        defaultProps={
          { data: tiktokAZ20260413Post2 } as unknown as Record<string, unknown>
        }
      />
      <Composition
        id="LinkedInCarousel"
        component={LinkedInCarousel as unknown as React.FC<Record<string, unknown>>}
        durationInFrames={8 * 30 * 3} // 8 slides × 3s × 30fps
        fps={30}
        width={theme.size.carousel.width}
        height={theme.size.carousel.height}
        defaultProps={
          { data: carouselData20260413 } as unknown as Record<string, unknown>
        }
      />
    </>
  );
};
