"use client";

/**
 * Public screening campaign landing page.
 *
 * Usage: /az/screening/<invite_token>
 *
 * Entry point of the B2B screening loop: an organization shares this link,
 * candidates land here, sign up (or log in) and join — which assigns them
 * the campaign's assessments. Decision: memory/decisions/2026-06-11-b2b-pivot.md
 */

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { motion } from "framer-motion";
import { ArrowRight, Building2, CheckCircle, ShieldCheck, XCircle } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { createClient } from "@/lib/supabase/client";
import { usePublicCampaign, useJoinCampaign } from "@/hooks/queries/use-campaigns";

export default function ScreeningLandingPage() {
  const { locale, token } = useParams<{ locale: string; token: string }>();
  const router = useRouter();
  const { t } = useTranslation();

  const { data: campaign, isLoading, error } = usePublicCampaign(token ?? null);
  const joinMutation = useJoinCampaign();

  const [joined, setJoined] = useState(false);
  // Surfaces a failure to provision the anonymous session (rare — Supabase down,
  // anonymous sign-ins disabled). Distinct from joinMutation's own error.
  const [authError, setAuthError] = useState(false);

  const nextPath = `/${locale}/screening/${token}`;

  // PM-anonymous flow: a candidate must be able to take the assessment WITHOUT a
  // VOLAURA account. We transparently create an anonymous Supabase session (mirrors
  // apps/v2 ensureSession, src/lib/client.ts:27-34) and then join. The backend
  // accepts anonymous JWTs for join + assessment (deps.py get_current_user_id
  // validates ANY valid Supabase token; no profile/email required).
  async function handleJoin() {
    setAuthError(false);
    try {
      const supabase = createClient();
      const { data } = await supabase.auth.getSession();
      if (!data.session) {
        const { error: anonError } = await supabase.auth.signInAnonymously();
        if (anonError) {
          setAuthError(true);
          return;
        }
      }
      const result = await joinMutation.mutateAsync(token);
      // Hand the campaign-assigned sessions to the runner so it activates THEM
      // (start WITH session_id) instead of a fresh off-campaign self-serve session.
      try {
        sessionStorage.setItem(
          `volaura-screening-plan:${token}`,
          JSON.stringify(result.sessions),
        );
      } catch {
        // sessionStorage unavailable (private mode quota) — runner re-joins idempotently.
      }
      setJoined(true);
    } catch {
      // error state rendered below via joinMutation.isError
    }
  }

  // ── Loading skeleton (matches final shape, no spinner) ───────────────────────
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background px-4">
        <div className="w-full max-w-md space-y-6 text-center">
          <Skeleton className="h-8 w-40 mx-auto" />
          <Skeleton className="h-6 w-64 mx-auto" />
          <Skeleton className="h-24 w-full rounded-xl" />
          <Skeleton className="h-12 w-full rounded-xl" />
        </div>
      </div>
    );
  }

  // ── Invalid / expired link ────────────────────────────────────────────────────
  if (error || !campaign) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background px-4">
        <div className="w-full max-w-md text-center space-y-6">
          <h1 className="text-2xl font-black tracking-tight text-foreground">VOLAURA</h1>
          <XCircle className="h-16 w-16 mx-auto text-[#D4B4FF]" />
          <div className="space-y-2">
            <h2 className="text-xl font-bold text-foreground">
              {t("screening.invalidTitle", { defaultValue: "This screening link is not valid." })}
            </h2>
            <p className="text-muted-foreground">
              {t("screening.invalidBody", {
                defaultValue: "The link may have expired. Ask the organization that sent it for a fresh one.",
              })}
            </p>
          </div>
          <Link
            href={`/${locale}`}
            className="inline-flex items-center justify-center gap-2 w-full rounded-xl border border-border bg-background px-7 py-3 text-sm font-medium text-muted-foreground transition-all hover:bg-accent"
          >
            {t("screening.goHome", { defaultValue: "Go to VOLAURA home" })}
          </Link>
        </div>
      </div>
    );
  }

  const closed = campaign.status !== "active";

  // ── Joined success state ──────────────────────────────────────────────────────
  if (joined) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-md text-center space-y-6"
        >
          <h1 className="text-2xl font-black tracking-tight text-foreground">VOLAURA</h1>
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.15, type: "spring" }}
            className="flex justify-center"
          >
            <CheckCircle className="h-16 w-16 text-green-500" />
          </motion.div>
          <div className="space-y-2">
            <h2 className="text-xl font-bold text-foreground">
              {t("screening.joinedTitle", { defaultValue: "You're in." })}
            </h2>
            <p className="text-muted-foreground">
              {t("screening.joinedBody", {
                defaultValue:
                  "Your assessments for {{org}} are ready. Complete them to appear in their candidate report.",
                org: campaign.org_name,
              })}
            </p>
          </div>
          <button
            onClick={() => router.push(`/${locale}/screening/${token}/run`)}
            className="inline-flex items-center justify-center gap-2 w-full rounded-xl bg-primary px-7 py-3.5 text-base font-semibold text-primary-foreground shadow-md transition-all hover:bg-primary/90"
          >
            {t("screening.startAssessments", { defaultValue: "Start your assessments" })}
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </button>
        </motion.div>
      </div>
    );
  }

  // ── Main landing ──────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4 py-10">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-md text-center space-y-6"
      >
        <div className="space-y-1">
          <h1 className="text-2xl font-black tracking-tight text-foreground">VOLAURA</h1>
          <p className="text-sm text-muted-foreground">
            {t("screening.tagline", { defaultValue: "Verified skills. Real evidence." })}
          </p>
        </div>

        <div className="rounded-2xl border border-border bg-card p-6 text-left space-y-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10">
              <Building2 className="h-5 w-5 text-primary" aria-hidden="true" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">
                {t("screening.invitedBy", { defaultValue: "Screening by" })}
              </p>
              <p className="text-sm font-semibold text-foreground">{campaign.org_name}</p>
            </div>
          </div>

          <div className="space-y-1">
            <h2 className="text-lg font-bold text-foreground">{campaign.title}</h2>
            {campaign.description && (
              <p className="text-sm text-muted-foreground whitespace-pre-line">{campaign.description}</p>
            )}
          </div>

          <div className="space-y-2">
            <p className="text-xs font-medium uppercase tracking-widest text-muted-foreground">
              {t("screening.competenciesLabel", { defaultValue: "You will be assessed on" })}
            </p>
            <div className="flex flex-wrap gap-2">
              {campaign.competency_slugs.map((slug) => (
                <span
                  key={slug}
                  className="inline-flex items-center gap-1 rounded-full border border-border bg-muted/40 px-3 py-1 text-xs text-foreground"
                >
                  <ShieldCheck className="h-3 w-3 text-primary" aria-hidden="true" />
                  {t(`competency.${slug}`, { defaultValue: slug.replace(/_/g, " ") })}
                </span>
              ))}
            </div>
          </div>
        </div>

        {closed ? (
          <p className="text-sm text-muted-foreground">
            {t("screening.closedBody", {
              defaultValue: "This screening is no longer accepting candidates.",
            })}
          </p>
        ) : campaign.is_full ? (
          <p className="text-sm text-muted-foreground">
            {t("screening.fullBody", {
              defaultValue: "This screening has reached its candidate limit.",
            })}
          </p>
        ) : (
          // One primary CTA — no account required. Join self-provisions an
          // anonymous session (handleJoin) so a PM can take the assessment without
          // signing up. "Already on VOLAURA? Log in" stays as a secondary link.
          <div className="space-y-3">
            <button
              onClick={handleJoin}
              disabled={joinMutation.isPending}
              className="inline-flex items-center justify-center gap-2 w-full rounded-xl bg-primary px-7 py-3.5 text-base font-semibold text-primary-foreground shadow-md transition-all hover:bg-primary/90 disabled:opacity-60"
            >
              {joinMutation.isPending
                ? t("screening.joining", { defaultValue: "Joining..." })
                : t("screening.joinCta", { defaultValue: "Join this screening" })}
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </button>
            {(joinMutation.isError || authError) && (
              <p className="text-sm text-[#D4B4FF]">
                {t("screening.joinError", {
                  defaultValue: "We couldn't join you right now — please try again in a moment.",
                })}
              </p>
            )}
            <p className="text-xs text-muted-foreground">
              {t("screening.haveAccount", { defaultValue: "Already on VOLAURA?" })}{" "}
              <Link
                href={`/${locale}/login?next=${encodeURIComponent(nextPath)}`}
                className="underline underline-offset-4 hover:text-foreground"
              >
                {t("screening.loginCta", { defaultValue: "Log in" })}
              </Link>
            </p>
          </div>
        )}

        <p className="text-xs text-muted-foreground">
          {t("screening.freeNote", {
            defaultValue: "Free for candidates. You keep your AURA profile and verified scores forever.",
          })}
        </p>
      </motion.div>
    </div>
  );
}
