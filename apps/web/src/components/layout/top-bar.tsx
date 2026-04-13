"use client";

import { useAuthStore } from "@/stores/auth-store";
import { LanguageSwitcher } from "./language-switcher";
import { Avatar } from "@/components/ui/avatar";
import { EnergyPicker, type EnergyLevel } from "@/components/assessment/energy-picker";
import { useEnergyMode } from "@/hooks/use-energy-mode";

/**
 * Top Bar — redesigned with energy picker + avatar
 *
 * Constitution:
 * - Law 2: compact energy picker always accessible
 * - Law 4: glass-header uses backdrop-blur
 *
 * Layout: [Avatar] Title ... [Energy] [Language]
 */

interface TopBarProps {
  title: string;
  /** Hide energy picker on specific pages (e.g., landing) */
  showEnergyPicker?: boolean;
}

export function TopBar({ title, showEnergyPicker = true }: TopBarProps) {
  const user = useAuthStore((s) => s.user);
  const { energy, setEnergy } = useEnergyMode();

  const displayName =
    user?.user_metadata?.display_name ??
    user?.email?.split("@")[0] ??
    "?";

  return (
    <>
      <header
        className="glass-header fixed top-0 flex h-14 w-full items-center justify-between px-4 shadow-sm"
        style={{ zIndex: "var(--z-sticky)" } as React.CSSProperties}
      >
        {/* Left: Avatar + Title */}
        <div className="flex items-center gap-3 min-w-0">
          {user && (
            <Avatar
              name={displayName}
              src={user.user_metadata?.avatar_url}
              tier="none"
              size="sm"
            />
          )}
          <h1 className="font-headline text-sm font-semibold text-foreground truncate">
            {title}
          </h1>
        </div>

        {/* Right: Energy + Language */}
        <div className="flex items-center gap-2 shrink-0">
          {showEnergyPicker && (
            <EnergyPicker
              value={energy}
              onChange={setEnergy}
              variant="compact"
            />
          )}
          <LanguageSwitcher />
        </div>
      </header>
      {/* Spacer */}
      <div className="h-14" aria-hidden="true" />
    </>
  );
}
