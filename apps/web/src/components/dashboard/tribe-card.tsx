"use client";

/**
 * Tribe Card — 3-person accountability circle widget.
 *
 * Design decisions encoded here:
 * - Q1: kudos_count = 0 → show "Be the first to send kudos" CTA, NEVER "0 kudos"
 * - Q2: crystal_fade_level drives opacity (0=bright, 1=slight dim, 2=dimmer)
 * - Q3: 2-person tribe is valid — renders normally with 2 members
 *
 * Anti-harassment: shows activity status only (active/inactive this week).
 * No AURA scores, no competency details, no streak comparison with others.
 */

import { useState } from "react";
import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";

import { cn } from "@/lib/utils/cn";
import {
  useMyTribe,
  useMyStreak,
  useMyPoolStatus,
  useSendKudos,
  useOptOutOfTribe,
  useRequestTribeRenewal,
  useJoinTribePool,
  type TribeMemberStatus,
} from "@/hooks/queries/use-tribes";

// Crystal opacity by fade level (Q2: fading crystal model)
const CRYSTAL_OPACITY: Record<0 | 1 | 2, string> = {
  0: "opacity-100",
  1: "opacity-60",
  2: "opacity-30",
};

export function TribeCard() {
  const { t } = useTranslation();
  const { data: tribe, isLoading: tribeLoading } = useMyTribe();
  const { data: poolStatus, isLoading: poolLoading } = useMyPoolStatus();
  const { data: streak } = useMyStreak();
  const sendKudos = useSendKudos();
  const optOut = useOptOutOfTribe();
  const requestRenewal = useRequestTribeRenewal();
  const joinPool = useJoinTribePool();
  const [showOptOutConfirm, setShowOptOutConfirm] = useState(false);

  if (tribeLoading || poolLoading) return null;

  // Waiting for match (persists across refreshes via DB state)
  if (!tribe && poolStatus?.in_pool) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-xl border border-violet-400/20 bg-gradient-to-br from-violet-500/5 to-indigo-500/5 p-4"
      >
        <div className="flex items-center gap-3">
          <motion.span
            className="text-2xl"
            aria-hidden="true"
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
          >
            🌀
          </motion.span>
          <div>
            <p className="text-sm font-semibold text-foreground">
              {t("tribe.findingTitle", { defaultValue: "Finding your tribe..." })}
            </p>
            <p className="text-xs text-muted-foreground">
              {t("tribe.joinedPool", { defaultValue: "You're in the pool! Matched within 24h." })}
            </p>
          </div>
        </div>
      </motion.div>
    );
  }

  // Not in a tribe and not in pool → show join CTA
  if (!tribe) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-xl border border-violet-400/20 bg-gradient-to-br from-violet-500/5 to-indigo-500/5 p-4"
      >
        <div className="flex items-center gap-3 mb-3">
          <span className="text-2xl" aria-hidden="true">🌀</span>
          <div>
            <p className="text-sm font-semibold text-foreground">
              {t("tribe.joinTitle", { defaultValue: "Join a Tribe" })}
            </p>
            <p className="text-xs text-muted-foreground">
              {t("tribe.joinDesc", { defaultValue: "3-person accountability circle. Stay consistent together." })}
            </p>
          </div>
        </div>
        <button
          onClick={() => joinPool.mutate()}
          disabled={joinPool.isPending}
          className="w-full rounded-lg bg-violet-500 hover:bg-violet-600 text-white text-sm font-medium py-2 transition-colors disabled:opacity-50"
        >
          {joinPool.isPending
            ? t("common.loading", { defaultValue: "..." })
            : t("tribe.joinCta", { defaultValue: "Find my tribe" })}
        </button>
      </motion.div>
    );
  }

  const fadeLevel = (streak?.crystal_fade_level ?? 0) as 0 | 1 | 2;
  const currentStreak = streak?.current_streak ?? 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-violet-400/20 bg-gradient-to-br from-violet-500/5 to-indigo-500/5 p-4 space-y-3"
    >
      {/* Header: streak crystal + count */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span
            className={cn("text-xl transition-opacity duration-700", CRYSTAL_OPACITY[fadeLevel])}
            aria-label={t("tribe.streakCrystal", { defaultValue: "Streak crystal" })}
          >
            💎
          </span>
          <div>
            <p className="text-sm font-semibold text-foreground leading-tight">
              {t("tribe.streakWeeks", { count: currentStreak, defaultValue: `${currentStreak} week streak` })}
            </p>
            {fadeLevel > 0 && (
              <p className="text-xs text-amber-500">
                {t("tribe.crystalFading", { defaultValue: "Keep your streak alive this week" })}
              </p>
            )}
          </div>
        </div>

        {/* Overflow menu */}
        <div className="relative">
          <OverflowMenu
            onOptOut={() => setShowOptOutConfirm(true)}
            onRenew={() => requestRenewal.mutate()}
            renewalRequested={tribe.renewal_requested}
            renewPending={requestRenewal.isPending}
            t={t}
          />
        </div>
      </div>

      {/* Members */}
      <div className="space-y-1.5">
        {tribe.members.map((member) => (
          <MemberRow key={member.user_id} member={member} t={t} />
        ))}
      </div>

      {/* Kudos section — Q1: hide count when 0, show CTA */}
      <KudosSection
        kudosCount={tribe.kudos_count_this_week}
        onSend={() => sendKudos.mutate()}
        isSending={sendKudos.isPending}
        isSent={sendKudos.isSuccess}
        t={t}
      />

      {/* Opt-out confirmation */}
      {showOptOutConfirm && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-3 space-y-2">
          <p className="text-xs text-foreground">
            {t("tribe.optOutConfirm", { defaultValue: "Leave this tribe? Your streak is safe — you can join a new tribe later." })}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => { optOut.mutate(); setShowOptOutConfirm(false); }}
              className="flex-1 rounded-md bg-destructive text-destructive-foreground text-xs py-1.5 font-medium"
            >
              {t("tribe.optOutConfirmYes", { defaultValue: "Leave tribe" })}
            </button>
            <button
              onClick={() => setShowOptOutConfirm(false)}
              className="flex-1 rounded-md border text-xs py-1.5"
            >
              {t("common.cancel", { defaultValue: "Cancel" })}
            </button>
          </div>
        </div>
      )}
    </motion.div>
  );
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function MemberRow({ member, t }: { member: TribeMemberStatus; t: (k: string, o?: object) => string }) {
  return (
    <div className="flex items-center gap-2.5">
      {/* Avatar */}
      <div className="relative shrink-0">
        {member.avatar_url ? (
          <img
            src={member.avatar_url}
            alt=""
            className="w-7 h-7 rounded-full object-cover"
          />
        ) : (
          <div className="w-7 h-7 rounded-full bg-muted flex items-center justify-center text-xs font-medium text-muted-foreground">
            {member.display_name.charAt(0).toUpperCase()}
          </div>
        )}
        {/* Activity dot */}
        <span
          className={cn(
            "absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-background",
            member.active_this_week ? "bg-emerald-500" : "bg-muted-foreground/30"
          )}
          aria-label={member.active_this_week
            ? t("tribe.memberActive", { defaultValue: "Active this week" })
            : t("tribe.memberInactive", { defaultValue: "Not active yet this week" })}
        />
      </div>
      <span className="text-xs text-foreground truncate flex-1">{member.display_name}</span>
      {member.active_this_week && (
        <span className="text-xs text-emerald-600 font-medium shrink-0">
          {t("tribe.memberActiveLabel", { defaultValue: "✓ active" })}
        </span>
      )}
    </div>
  );
}

function KudosSection({
  kudosCount,
  onSend,
  isSending,
  isSent,
  t,
}: {
  kudosCount: number;
  onSend: () => void;
  isSending: boolean;
  isSent: boolean;
  t: (k: string, o?: object) => string;
}) {
  // Q1: if count = 0, show CTA — NEVER show "0 kudos"
  return (
    <div className="flex items-center justify-between pt-1 border-t border-border/40">
      <div className="text-xs text-muted-foreground">
        {kudosCount > 0 ? (
          <span>
            {t("tribe.kudosCount", { count: kudosCount, defaultValue: `${kudosCount} kudos this week` })}
          </span>
        ) : (
          <span>{t("tribe.kudosBeFirst", { defaultValue: "Be the first to send kudos" })}</span>
        )}
      </div>
      <button
        onClick={onSend}
        disabled={isSending || isSent}
        className={cn(
          "text-xs px-3 py-1 rounded-full border transition-colors",
          isSent
            ? "bg-emerald-50 border-emerald-300 text-emerald-600 cursor-default"
            : "hover:bg-accent border-border text-foreground"
        )}
      >
        {isSent
          ? t("tribe.kudosSent", { defaultValue: "Sent ✓" })
          : t("tribe.kudosSend", { defaultValue: "Send kudos" })}
      </button>
    </div>
  );
}

function OverflowMenu({
  onOptOut,
  onRenew,
  renewalRequested,
  renewPending,
  t,
}: {
  onOptOut: () => void;
  onRenew: () => void;
  renewalRequested: boolean;
  renewPending: boolean;
  t: (k: string, o?: object) => string;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="p-1 rounded-md hover:bg-accent text-muted-foreground text-sm"
        aria-label={t("common.moreOptions", { defaultValue: "More options" })}
      >
        ···
      </button>
      {open && (
        <div
          className="absolute right-0 top-6 z-10 w-44 rounded-lg border bg-popover shadow-md py-1"
          onMouseLeave={() => setOpen(false)}
        >
          {/* Q3: opt-out first item — 1-tap, no confirmation until press */}
          <button
            onClick={() => { onOptOut(); setOpen(false); }}
            className="w-full text-left text-xs px-3 py-2 hover:bg-accent text-destructive"
          >
            {t("tribe.optOut", { defaultValue: "Leave this tribe" })}
          </button>
          <button
            onClick={() => { onRenew(); setOpen(false); }}
            disabled={renewalRequested || renewPending}
            className="w-full text-left text-xs px-3 py-2 hover:bg-accent text-foreground disabled:opacity-40"
          >
            {renewalRequested
              ? t("tribe.renewalRequested", { defaultValue: "Renewal requested ✓" })
              : t("tribe.requestRenewal", { defaultValue: "Request renewal" })}
          </button>
        </div>
      )}
    </div>
  );
}
