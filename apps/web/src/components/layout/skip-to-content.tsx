"use client";

import { useTranslation } from "react-i18next";

/**
 * Skip-to-content link — WCAG 2.2 2.4.1 Bypass Blocks (AA).
 *
 * Landed 2026-04-15 per Phase 1 gap-matrix TIER-0 #5 (ghost-audit a11y P0-5).
 * Keyboard users previously had to tab through all 11 sidebar items + 5
 * bottom-tab items on every page load before reaching main content.
 *
 * Visually hidden by default (sr-only). When keyboard-focused (Tab on page
 * load), becomes visible as a pill-styled link in the top-left corner —
 * clicking or Enter jumps focus to `<main id="main-content">`.
 *
 * Uses `focus-visible:` so mouse clicks don't trigger the visible state.
 */
export function SkipToContent() {
  const { t } = useTranslation();
  return (
    <a
      href="#main-content"
      className="sr-only focus:not-sr-only focus-visible:fixed focus-visible:top-2 focus-visible:left-2 focus-visible:z-[999] focus-visible:rounded-lg focus-visible:bg-primary focus-visible:px-4 focus-visible:py-2 focus-visible:text-on-primary focus-visible:shadow-lg focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
    >
      {t("a11y.skipToContent", { defaultValue: "Əsas məzmuna keç" })}
    </a>
  );
}
