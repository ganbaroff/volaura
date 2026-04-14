"use client";

import { cn } from "@/lib/utils/cn";

/**
 * Avatar — badge tier with visual distinction
 *
 * Design: open-questions-resolved.md Q3
 * - Phase 1: Static SVG per tier (no composable parts)
 * - Bronze: muted, no glow
 * - Silver: subtle shimmer border
 * - Gold: warm glow (#E9C400 at 0.3 opacity)
 * - Platinum: full glow + CSS particles (3 max)
 * - Fallback: initials on surface-container-high
 */

type BadgeTier = "platinum" | "gold" | "silver" | "bronze" | "none";
type AvatarSize = "sm" | "md" | "lg" | "xl";

interface AvatarProps {
  /** User display name for initials fallback */
  name: string;
  /** Image URL (optional) */
  src?: string | null;
  /** Badge tier determines glow effect */
  tier?: BadgeTier;
  /** Size */
  size?: AvatarSize;
  className?: string;
}

const sizeClasses: Record<AvatarSize, string> = {
  sm: "h-8 w-8 text-xs",
  md: "h-10 w-10 text-sm",
  lg: "h-14 w-14 text-base",
  xl: "h-20 w-20 text-xl",
};

const tierGlows: Record<BadgeTier, string> = {
  platinum: "badge-glow-platinum ring-2 ring-aura-platinum/30",
  gold: "badge-glow-gold ring-2 ring-aura-gold/30",
  silver: "badge-glow-silver ring-1 ring-aura-silver/20",
  bronze: "ring-1 ring-aura-bronze/15",
  none: "",
};

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((part) => part[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

export function Avatar({
  name,
  src,
  tier = "none",
  size = "md",
  className,
}: AvatarProps) {
  const initials = getInitials(name);

  return (
    <div
      className={cn(
        "relative inline-flex items-center justify-center rounded-full overflow-hidden",
        "bg-surface-container-high text-on-surface font-headline font-bold",
        sizeClasses[size],
        tierGlows[tier],
        className,
      )}
      role="img"
      aria-label={name}
    >
      {src ? (
        // eslint-disable-next-line @next/next/no-img-element -- avatar src may be from OAuth CDNs (Google, GitHub, etc.) outside remotePatterns; native img handles arbitrary URLs safely with lazy loading
        <img
          src={src}
          alt={name}
          className="h-full w-full object-cover"
          loading="lazy"
        />
      ) : (
        <span aria-hidden="true">{initials}</span>
      )}

      {/* Platinum particle effect (CSS-only, max 3 particles, Law 4 safe) */}
      {tier === "platinum" && (
        <>
          <span className="absolute -top-0.5 -right-0.5 h-1.5 w-1.5 rounded-full bg-aura-platinum/60 animate-float" />
          <span className="absolute -bottom-0.5 -left-0.5 h-1 w-1 rounded-full bg-primary/40 animate-float-delayed" />
          <span className="absolute top-0 left-1/2 h-1 w-1 rounded-full bg-aura-platinum/30 animate-float-more-delayed" />
        </>
      )}
    </div>
  );
}
