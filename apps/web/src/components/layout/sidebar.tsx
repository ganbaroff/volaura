"use client";

import Link from "next/link";
import { usePathname, useParams } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { useState, useEffect, useCallback } from "react";
import { useUnreadCount } from "@/hooks/queries/use-notifications";
import { useProfile } from "@/hooks/queries/use-profile";

type NavItem = { href: string; labelKey: string; icon: string; orgOnly?: boolean };

const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard",      labelKey: "nav.dashboard",      icon: "⊞" },
  { href: "/profile",        labelKey: "nav.profile",        icon: "◉" },
  { href: "/aura",           labelKey: "nav.aura",           icon: "◈" },
  { href: "/assessment",     labelKey: "nav.assessment",     icon: "◑" },
  { href: "/brandedby",      labelKey: "nav.brandedby",      icon: "✦" },
  { href: "/events",         labelKey: "nav.events",         icon: "◎" },
  { href: "/my-organization", labelKey: "nav.myOrganization", icon: "🏢", orgOnly: true },
  { href: "/org-volunteers",  labelKey: "nav.orgVolunteers",  icon: "👥", orgOnly: true },
  { href: "/discover",        labelKey: "nav.discover",       icon: "🔍", orgOnly: true },
  // Leaderboard nav removed 2026-04-12 — Constitution v1.7 G9/G46.
  { href: "/notifications",  labelKey: "nav.notifications",  icon: "🔔" },
  { href: "/settings",       labelKey: "nav.settings",       icon: "◧" },
];

export function Sidebar() {
  const { locale } = useParams<{ locale: string }>();
  const pathname = usePathname();
  const router = useRouter();
  const clear = useAuthStore((s) => s.clear);
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const { data: unreadData } = useUnreadCount();
  const unreadCount = unreadData?.unread_count ?? 0;
  const { data: profile } = useProfile();
  const isOrg = (profile as { account_type?: string } | undefined)?.account_type === "organization";

  // Close sidebar on route change (mobile)
  useEffect(() => {
    setIsOpen(false);
  }, [pathname]);

  // Close on Escape key
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === "Escape") setIsOpen(false);
  }, []);

  useEffect(() => {
    if (isOpen) {
      document.addEventListener("keydown", handleKeyDown);
      return () => document.removeEventListener("keydown", handleKeyDown);
    }
  }, [isOpen, handleKeyDown]);

  async function handleLogout() {
    const supabase = createClient();
    await supabase.auth.signOut();
    clear();
    router.push(`/${locale}/login`);
  }

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        onClick={() => setIsOpen(true)}
        aria-label={t("nav.openMenu")}
        className="relative fixed left-3 top-3 z-[60] flex size-11 items-center justify-center rounded-xl bg-surface-container text-on-surface md:hidden"
      >
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
          <path d="M3 5h14M3 10h14M3 15h14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
        {/* Unread notification dot — visible when there are unread notifications */}
        {unreadCount > 0 && (
          <span
            aria-label={`${unreadCount} unread notifications`}
            className="absolute top-1.5 right-1.5 size-2.5 rounded-full bg-primary"
          />
        )}
      </button>

      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={() => setIsOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        role="navigation"
        aria-label={t("nav.mainNavigation")}
        className={`fixed inset-y-0 left-0 z-50 flex w-56 flex-shrink-0 flex-col bg-surface-container-low px-3 py-4 transition-transform duration-200 ease-in-out md:relative md:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Logo + close button (mobile) */}
        <div className="mb-6 flex items-center justify-between px-2">
          <Link
            href={`/${locale}/dashboard`}
            className="font-headline text-lg font-bold text-primary"
          >
            Volaura
          </Link>
          <button
            onClick={() => setIsOpen(false)}
            aria-label={t("nav.closeMenu")}
            className="flex size-8 items-center justify-center rounded-lg text-on-surface-variant hover:bg-surface-container md:hidden"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
              <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 space-y-1">
          {NAV_ITEMS.filter((item) => !item.orgOnly || isOrg).map(({ href, labelKey, icon }) => {
            const fullHref = `/${locale}${href}`;
            const isActive = pathname === fullHref || pathname.startsWith(`${fullHref}/`);
            const isNotifications = href === "/notifications";
            const badge = isNotifications && unreadCount > 0
              ? Math.min(unreadCount, 99)
              : null;
            return (
              <Link
                key={href}
                href={fullHref}
                aria-current={isActive ? "page" : undefined}
                className={`flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-surface-container-high text-primary"
                    : "text-on-surface-variant hover:bg-surface-container hover:text-on-surface"
                }`}
              >
                <span className="text-base" aria-hidden="true">{icon}</span>
                <span className="flex-1">{t(labelKey)}</span>
                {badge !== null && (
                  <span
                    aria-label={`${badge} unread`}
                    className="inline-flex items-center justify-center min-w-[18px] h-[18px] rounded-full bg-primary text-on-primary text-[10px] font-bold px-1"
                  >
                    {badge > 99 ? "99+" : badge}
                  </span>
                )}
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
          <span className="text-base" aria-hidden="true">→</span>
          {t("auth.logout")}
        </button>
      </aside>
    </>
  );
}
