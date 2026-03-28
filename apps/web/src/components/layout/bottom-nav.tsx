"use client";

import Link from "next/link";
import { usePathname, useParams } from "next/navigation";
import { useTranslation } from "react-i18next";

// 5 primary destinations for mobile — thumb-reach bottom nav (ADHD-first design)
// Remaining items (events, brandedby, org, settings) accessible via sidebar
const BOTTOM_NAV_ITEMS = [
  { href: "/dashboard",  labelKey: "nav.dashboard",  icon: "⊞" },
  { href: "/aura",       labelKey: "nav.aura",       icon: "◈" },
  { href: "/assessment", labelKey: "nav.assessment", icon: "◑" },
  { href: "/profile",    labelKey: "nav.profile",    icon: "◉" },
  { href: "/leaderboard", labelKey: "nav.leaderboard", icon: "🏆" },
] as const;

export function BottomNav() {
  const params = useParams<{ locale: string }>();
  const locale = params?.locale ?? "az";
  const pathname = usePathname();
  const { t } = useTranslation();

  return (
    <nav
      role="navigation"
      aria-label={t("nav.mainNavigation")}
      // visible only on mobile (md and up = desktop sidebar handles navigation)
      className="fixed bottom-0 left-0 right-0 z-40 flex h-[72px] items-stretch border-t border-surface-container bg-surface-container-low md:hidden"
    >
      {BOTTOM_NAV_ITEMS.map(({ href, labelKey, icon }) => {
        const fullHref = `/${locale}${href}`;
        const isActive =
          pathname === fullHref || pathname.startsWith(`${fullHref}/`);

        return (
          <Link
            key={href}
            href={fullHref}
            aria-current={isActive ? "page" : undefined}
            // min 48px tap target via flex-1 + h-full
            className="flex flex-1 flex-col items-center justify-center gap-0.5 transition-colors"
          >
            {/* Icon: larger + colored when active */}
            <span
              className={`text-2xl leading-none transition-colors ${
                isActive ? "text-primary" : "text-on-surface-variant"
              }`}
              aria-hidden="true"
            >
              {icon}
            </span>

            {/* Label: always visible (ADHD-first — no hidden labels) */}
            <span
              className={`text-[10px] font-medium leading-none transition-colors ${
                isActive ? "text-primary" : "text-on-surface-variant"
              }`}
            >
              {t(labelKey)}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
