"use client";

import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import { MapPin, Globe, Lock, Pencil, Eye } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils/cn";
import { Avatar } from "@/components/ui/avatar";

export interface ProfileHeaderData {
  display_name: string | null;
  username: string;
  bio: string | null;
  location: string | null;
  languages: string[];
  is_public: boolean;
  avatar_url: string | null;
  badge_tier?: "platinum" | "gold" | "silver" | "bronze" | "none";
  total_score?: number | null;
  registration_number?: number | null;
  registration_tier?: string | null;
}

interface ProfileHeaderProps {
  profile: ProfileHeaderData;
  locale: string;
  isOwnProfile?: boolean;
}

// TIER_RING moved to Avatar component (components/ui/avatar.tsx)

export function ProfileHeader({ profile, locale, isOwnProfile }: ProfileHeaderProps) {
  const { t } = useTranslation();
  const displayName = profile.display_name ?? profile.username;
  const tier = profile.badge_tier ?? "none";

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="flex items-start gap-4"
    >
      {/* Avatar — design system component with badge tier glows */}
      <Avatar
        name={displayName}
        src={profile.avatar_url}
        tier={tier as "platinum" | "gold" | "silver" | "bronze" | "none"}
        size="lg"
        className="shrink-0"
      />

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <h2 className="text-lg font-bold text-foreground truncate">{displayName}</h2>
            <p className="text-sm text-muted-foreground truncate">@{profile.username}</p>
            {profile.registration_number != null && (
              <p className="text-xs text-muted-foreground font-mono mt-0.5">
                #{String(profile.registration_number).padStart(4, "0")}
                {profile.registration_tier === "founding_100" && (
                  <span className="ml-2 text-xs font-medium text-amber-500">
                    {t("profile.foundingMember")}
                  </span>
                )}
                {profile.registration_tier === "founding_1000" && (
                  <span className="ml-2 text-xs font-medium text-cyan-400">
                    {t("profile.founding1000")}
                  </span>
                )}
                {profile.registration_tier === "early_adopter" && (
                  <span className="ml-2 text-xs font-medium text-blue-400">
                    {t("profile.earlyAdopter")}
                  </span>
                )}
              </p>
            )}
          </div>

          {isOwnProfile && (
            <Link
              href={`/${locale}/profile/edit`}
              aria-label={t("profile.editProfile")}
              className="shrink-0 size-8 rounded-full border border-border bg-card flex items-center justify-center hover:bg-accent transition-colors"
            >
              <Pencil className="size-3.5 text-muted-foreground" />
            </Link>
          )}
        </div>

        {/* AURA score + badge + visibility */}
        {(profile.total_score != null || tier !== "none") && (
          <div className="mt-1.5 flex items-center gap-2">
            {profile.total_score != null && (
              <span className="text-lg font-bold text-foreground tabular-nums">
                {Math.round(profile.total_score)}
              </span>
            )}
            {tier !== "none" && (
              <span className={cn(
                "rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide",
                tier === "platinum" && "bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-300",
                tier === "gold" && "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300",
                tier === "silver" && "bg-slate-100 text-slate-600 dark:bg-slate-800/40 dark:text-slate-300",
                tier === "bronze" && "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
              )}>
                {t(`badge.${tier}`, { defaultValue: tier })}
              </span>
            )}
          </div>
        )}

        {profile.bio && (
          <p className="mt-1.5 text-sm text-foreground leading-snug line-clamp-2">
            {profile.bio}
          </p>
        )}

        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1">
          {profile.location && (
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <MapPin className="size-3" aria-hidden="true" />
              {profile.location}
            </span>
          )}
          {profile.languages.length > 0 && (
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <Globe className="size-3" aria-hidden="true" />
              {profile.languages.join(", ")}
            </span>
          )}
          {profile.is_public ? (
            <span className="flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-400">
              <Eye className="size-3" aria-hidden="true" />
              {t("profile.discoverable", { defaultValue: "Discoverable by organizations" })}
            </span>
          ) : (
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <Lock className="size-3" aria-hidden="true" />
              {t("profile.private")}
            </span>
          )}
        </div>
      </div>
    </motion.div>
  );
}
