"use client";

import { usePathname } from "next/navigation";
import { useTranslation } from "react-i18next";
import { cn } from "@/lib/utils/cn";

/**
 * Bottom Tab Bar — Discord-style product switcher
 *
 * Constitution compliance:
 * - Law 4: 150ms tab transitions, spring damping ≥14
 * - Law 5: Tab bar = navigation only, never a CTA
 *
 * ADHD rules:
 * - Clear structure, predictable layout
 * - Immediate feedback on tap (<100ms visual response)
 *
 * Design: ecosystem-design-research.md "Discord Three-Rail"
 * - Active tab uses product accent color (Tier 3 token)
 * - Labels always visible (no icon-only tabs — ADHD clarity)
 */

type Product = "volaura" | "aura" | "mindshift" | "lifesim" | "brandedby" | "atlas";

interface TabItem {
  id: Product;
  labelKey: string;
  defaultLabel: string;
  icon: React.ReactNode;
  href: string;
  accentVar: string;
}

// Feature flags — tabs only appear when the corresponding page is enabled.
const MINDSHIFT_ENABLED = process.env.NEXT_PUBLIC_ENABLE_MINDSHIFT === "true";
const ATLAS_ENABLED = process.env.NEXT_PUBLIC_ENABLE_ATLAS === "true";

const ALL_TABS: (TabItem & { enabled?: boolean })[] = [
  {
    id: "volaura",
    labelKey: "nav.volaura",
    defaultLabel: "Home",
    icon: <HomeIcon />,
    href: "/",
    accentVar: "var(--color-product-volaura)",
  },
  {
    id: "aura",
    labelKey: "nav.aura",
    defaultLabel: "AURA",
    icon: <RadarIcon />,
    href: "/aura",
    accentVar: "var(--color-product-volaura)",
  },
  {
    id: "mindshift",
    labelKey: "nav.mindshift",
    defaultLabel: "MindShift",
    icon: <BrainIcon />,
    href: "/mindshift",
    accentVar: "var(--color-product-mindshift)",
    enabled: MINDSHIFT_ENABLED,
  },
  {
    id: "lifesim",
    labelKey: "nav.lifesim",
    defaultLabel: "Life Sim",
    icon: <GameIcon />,
    href: "/life",
    accentVar: "var(--color-product-lifesim)",
  },
  {
    id: "atlas",
    labelKey: "nav.atlas",
    defaultLabel: "ATLAS",
    icon: <BoltIcon />,
    href: "/atlas",
    accentVar: "var(--color-product-atlas-system)",
    enabled: ATLAS_ENABLED,
  },
];

const TABS: TabItem[] = ALL_TABS.filter((tab) => tab.enabled !== false);

interface BottomTabBarProps {
  /** Override locale (optional — defaults to URL param) */
  locale?: string;
}

export function BottomTabBar({ locale: localeProp }: BottomTabBarProps) {
  const pathname = usePathname();
  const { t } = useTranslation();
  // Get locale from URL params if not passed as prop (same pattern as old BottomNav)
  const locale = localeProp ?? pathname.split("/")[1] ?? "az";

  const getActiveTab = (): string => {
    const path = pathname.replace(`/${locale}`, "") || "/";
    if (path.startsWith("/mindshift")) return "/mindshift";
    if (path.startsWith("/life")) return "/life";
    if (path.startsWith("/atlas")) return "/atlas";
    if (path.startsWith("/aura")) return "/aura";
    return "/";
  };

  const activeHref = getActiveTab();

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 glass-nav border-t border-border/50 safe-area-bottom md:hidden"
      style={{ zIndex: "var(--z-bottomnav)" } as React.CSSProperties}
      aria-label={t("nav.productSwitcher", { defaultValue: "Product navigation" })}
    >
      <div className="mx-auto flex max-w-md items-center justify-around px-2 py-1">
        {TABS.map((tab) => {
          const isActive = tab.href === activeHref;
          return (
            <a
              key={tab.href}
              href={`/${locale}${tab.href === "/" ? "" : tab.href}`}
              aria-current={isActive ? "page" : undefined}
              aria-label={t(tab.labelKey, { defaultValue: tab.defaultLabel })}
              className={cn(
                "flex flex-col items-center gap-0.5 px-3 py-2 rounded-xl",
                "transition-all energy-target",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
                isActive
                  ? "text-foreground"
                  : "text-muted-foreground hover:text-foreground/80"
              )}
              style={{
                transitionDuration: "var(--duration-fast)",
                ...(isActive ? { color: tab.accentVar } : {}),
              } as React.CSSProperties}
            >
              <span
                className={cn(
                  "flex h-6 w-6 items-center justify-center",
                  isActive && "animate-tab-slide"
                )}
              >
                {tab.icon}
              </span>
              <span className="text-[10px] font-medium leading-none">
                {t(tab.labelKey, { defaultValue: tab.defaultLabel })}
              </span>
              {isActive && (
                <span
                  className="absolute -bottom-0.5 h-0.5 w-4 rounded-full"
                  style={{ backgroundColor: tab.accentVar } as React.CSSProperties}
                />
              )}
            </a>
          );
        })}
      </div>
    </nav>
  );
}

/* ── Inline SVG icons (no external dependency, 0KB extra) ── */

function HomeIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
      <polyline points="9 22 9 12 15 12 15 22" />
    </svg>
  );
}

function RadarIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26" />
    </svg>
  );
}

function BrainIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a7 7 0 017 7c0 2.38-1.19 4.47-3 5.74V17a2 2 0 01-2 2h-4a2 2 0 01-2-2v-2.26C6.19 13.47 5 11.38 5 9a7 7 0 017-7z" />
      <line x1="9" y1="22" x2="15" y2="22" />
    </svg>
  );
}

function GameIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="6" width="20" height="12" rx="2" />
      <line x1="6" y1="12" x2="6.01" y2="12" />
      <line x1="10" y1="12" x2="10.01" y2="12" />
      <path d="M15 9h3v6" />
      <path d="M15 12h3" />
    </svg>
  );
}

function BoltIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10" />
    </svg>
  );
}
