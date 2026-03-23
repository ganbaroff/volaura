"use client";

import Link from "next/link";
import { usePathname, useParams } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";

const NAV_ITEMS = [
  { href: "/dashboard",      labelKey: "nav.dashboard",      icon: "⊞" },
  { href: "/profile",        labelKey: "nav.profile",        icon: "◉" },
  { href: "/aura",           labelKey: "nav.aura",           icon: "◈" },
  { href: "/assessment",     labelKey: "nav.assessment",     icon: "◑" },
  { href: "/events",         labelKey: "nav.events",         icon: "◎" },
  { href: "/my-organization", labelKey: "nav.myOrganization", icon: "🏢" },
  { href: "/leaderboard",    labelKey: "nav.leaderboard",    icon: "🏆" },
  { href: "/notifications",  labelKey: "nav.notifications",  icon: "🔔" },
  { href: "/settings",       labelKey: "nav.settings",       icon: "◧" },
] as const;

export function Sidebar() {
  const { locale } = useParams<{ locale: string }>();
  const pathname = usePathname();
  const router = useRouter();
  const clear = useAuthStore((s) => s.clear);
  const { t } = useTranslation();

  async function handleLogout() {
    const supabase = createClient();
    await supabase.auth.signOut();
    clear();
    router.push(`/${locale}/login`);
  }

  return (
    <aside className="flex h-full w-56 flex-shrink-0 flex-col bg-surface-container-low px-3 py-4">
      {/* Logo */}
      <Link
        href={`/${locale}/dashboard`}
        className="mb-6 px-2 font-headline text-lg font-bold text-primary"
      >
        Volaura
      </Link>

      {/* Nav */}
      <nav className="flex-1 space-y-1">
        {NAV_ITEMS.map(({ href, labelKey, icon }) => {
          const fullHref = `/${locale}${href}`;
          const isActive = pathname === fullHref || pathname.startsWith(`${fullHref}/`);
          return (
            <Link
              key={href}
              href={fullHref}
              className={`flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-surface-container-high text-primary"
                  : "text-on-surface-variant hover:bg-surface-container hover:text-on-surface"
              }`}
            >
              <span className="text-base">{icon}</span>
              {t(labelKey)}
            </Link>
          );
        })}
      </nav>

      {/* Logout */}
      <button
        onClick={handleLogout}
        aria-label={t("auth.logout")}
        className="flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm font-medium text-on-surface-variant transition-colors hover:bg-error-container/20 hover:text-error"
      >
        <span className="text-base">→</span>
        {t("auth.logout")}
      </button>
    </aside>
  );
}
