"use client";

import { useAuthStore } from "@/stores/auth-store";
import { LanguageSwitcher } from "./language-switcher";

interface TopBarProps {
  title: string;
}

export function TopBar({ title }: TopBarProps) {
  const user = useAuthStore((s) => s.user);

  return (
    <>
      <header className="glass-header fixed top-0 z-50 flex h-16 w-full items-center justify-between px-6 pl-14 md:pl-6 shadow-[0_4px_20px_rgba(0,0,0,0.3)]">
        <h1 className="font-headline text-base font-semibold text-primary">{title}</h1>
        <div className="flex items-center gap-3">
          <LanguageSwitcher />
          {user && (
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-primary to-primary-container text-xs font-bold text-on-primary shadow-[0_0_12px_rgba(192,193,255,0.3)]">
              {(user.email ?? "?")[0].toUpperCase()}
            </div>
          )}
        </div>
      </header>
      {/* Spacer: pushes page content below the fixed 64px header */}
      <div className="h-16" aria-hidden="true" />
    </>
  );
}
