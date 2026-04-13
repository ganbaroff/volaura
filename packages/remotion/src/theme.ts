/**
 * VOLAURA ecosystem design tokens for video compositions.
 * Mirrors apps/web globals.css. Constitution v1.7 compliant.
 *
 * RULES:
 *  - NEVER RED. Errors / alerts use purple #D4B4FF, warnings #E9C400.
 *  - Max 800ms non-decorative animation durations.
 *  - One primary CTA per frame.
 *  - Character / mascot animations: state-machine driven (see Rive when mascot added).
 */

export const theme = {
  color: {
    // Surfaces (Obsidian glass dark theme)
    bg: "#13131b",
    bgElevated: "#1a1a26",
    bgGlass: "rgba(26, 26, 38, 0.64)",

    // Text
    text: "#EDEEF5",
    textMuted: "#9CA0B8",
    textDim: "#6B6F88",

    // Product accent colors (Constitution)
    volaura: "#c0c1ff", // indigo
    mindshift: "#10B981", // emerald
    lifeSim: "#7C3AED", // purple
    brandedBy: "#0EA5E9", // sky
    zeus: "#E9C400", // gold

    // Semantic
    error: "#D4B4FF", // purple — NEVER red
    warning: "#E9C400", // amber
    success: "#10B981",

    // Badge tiers (per Constitution)
    bronze: "#CD7F32",
    silver: "#C0C0C0",
    gold: "#EAB308",
    platinum: "#A78BFA",
  },

  font: {
    sans: '"Plus Jakarta Sans", "Inter", -apple-system, BlinkMacSystemFont, sans-serif',
    body: '"Inter", -apple-system, sans-serif',
    display: '"Plus Jakarta Sans", sans-serif',
    mono: '"JetBrains Mono", ui-monospace, monospace',
  },

  size: {
    // Vertical TikTok / Reels
    tiktok: { width: 1080, height: 1920 },
    // Horizontal YouTube
    youtube: { width: 1920, height: 1080 },
    // Square post
    square: { width: 1080, height: 1080 },
    // LinkedIn carousel slide (portrait 4:5)
    carousel: { width: 1080, height: 1350 },
  },

  motion: {
    // Constitution Law 4 — max 800ms non-decorative
    short: 200, // ms
    medium: 400,
    long: 600,
    max: 800,
  },
} as const;

export type Theme = typeof theme;
