"use client";

import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { LayoutDashboard, Users, Building2, Star, Bot, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils/cn";

const NAV_ITEMS = [
  { href: "",              label: "Overview",      icon: LayoutDashboard },
  { href: "/swarm",        label: "AI Office",     icon: Bot             },
  { href: "/users",        label: "Users",         icon: Users           },
  { href: "/organizations",label: "Organizations", icon: Building2       },
  { href: "/aura",         label: "AURA Scores",   icon: Star            },
];

export function AdminSidebar() {
  const { locale } = useParams<{ locale: string }>();
  const pathname = usePathname();
  const base = `/${locale}/admin`;

  return (
    <aside className="hidden md:flex flex-col w-56 shrink-0 border-r border-border bg-surface-container-low h-screen sticky top-0">
      {/* Brand */}
      <div className="flex items-center gap-2 px-4 py-5 border-b border-border">
        <ShieldCheck className="size-5 text-primary" aria-hidden="true" />
        <span className="text-sm font-bold text-on-surface">Admin Panel</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 py-4 space-y-1" aria-label="Admin navigation">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const to = `${base}${href}`;
          const isActive = href === "" ? pathname === base : pathname.startsWith(to);
          return (
            <Link
              key={href}
              href={to}
              className={cn(
                "flex items-center gap-2.5 rounded-xl px-3 py-2 text-sm transition-colors",
                isActive
                  ? "bg-primary/10 text-primary font-semibold"
                  : "text-on-surface-variant hover:bg-surface-container hover:text-on-surface"
              )}
              aria-current={isActive ? "page" : undefined}
            >
              <Icon className="size-4 shrink-0" aria-hidden="true" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Back to app */}
      <div className="p-3 border-t border-border">
        <Link
          href={`/${locale}/dashboard`}
          className="flex items-center gap-2 rounded-xl px-3 py-2 text-xs text-on-surface-variant hover:text-on-surface hover:bg-surface-container transition-colors"
        >
          ← Back to app
        </Link>
      </div>
    </aside>
  );
}
