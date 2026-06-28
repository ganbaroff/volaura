"use client";

/**
 * Campaign report — ranked candidate list for one screening campaign.
 *
 * Ranking (computed server-side): most completed assessments first,
 * then campaign score (mean of campaign competencies), then earliest joined.
 *
 * Org-billing: when the report endpoint returns 402 PAYMENT_REQUIRED
 * (org_billing_enabled flag on AND org lacks access) we show a paywall
 * upsell instead of the generic error. Dormant while the flag is off.
 */

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { ArrowLeft, Award, CheckCircle2, Clock, ExternalLink, Sparkles } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils/cn";
import { apiFetch } from "@/lib/api/client";
import { useCampaignReport, type CandidateReportRow } from "@/hooks/queries/use-campaigns";

const TIER_STYLES: Record<string, string> = {
  platinum: "bg-violet-500/10 text-violet-400",
  gold: "bg-amber-500/10 text-amber-400",
  silver: "bg-slate-400/10 text-slate-300",
  bronze: "bg-orange-500/10 text-orange-400",
};

export default function CampaignReportPage() {
  const { locale, id } = useParams<{ locale: string; id: string }>();
  const { t } = useTranslation();
  const { data, isLoading, error } = useCampaignReport(id ?? null);

  // 402 PAYMENT_REQUIRED → org-billing paywall. Detect on either signal
  // (HTTP status or FastAPI detail.code). Defensive cast keeps this robust to
  // the hook's error generic. Dormant: the flag is off in prod, so this never
  // fires today (report returns 200); it activates when the CEO flips it.
  const apiErr = error as { status?: number; code?: string } | null;
  const paymentRequired = apiErr != null && (apiErr.status === 402 || apiErr.code === "PAYMENT_REQUIRED");

  if (isLoading) {
    return (
      <div className="mx-auto w-full max-w-3xl space-y-4 px-4 py-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-5 w-80" />
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-20 w-full rounded-xl" />
        ))}
      </div>
    );
  }

  if (paymentRequired && id) {
    return <ReportPaywall campaignId={id} locale={locale} />;
  }

  if (error || !data) {
    return (
      <div className="mx-auto w-full max-w-3xl px-4 py-10 text-center space-y-4">
        <p className="text-sm text-foreground">
          {t("campaigns.reportError", {
            defaultValue: "We couldn't load this report — it may not exist, or it belongs to another organization.",
          })}
        </p>
        <Link
          href={`/${locale}/my-organization/campaigns`}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-primary underline-offset-4 hover:underline"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          {t("campaigns.backToList", { defaultValue: "Back to campaigns" })}
        </Link>
      </div>
    );
  }

  const { campaign, candidates } = data;

  return (
    <div className="mx-auto w-full max-w-3xl space-y-6 px-4 py-6">
      <div className="space-y-2">
        <Link
          href={`/${locale}/my-organization/campaigns`}
          className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
          {t("campaigns.backToList", { defaultValue: "Back to campaigns" })}
        </Link>
        <h1 className="text-2xl font-bold font-headline text-foreground">{campaign.title}</h1>
        <p className="text-sm text-muted-foreground">
          {t("campaigns.reportMeta", {
            defaultValue: "{{joined}} candidates · {{completed}} finished all assessments",
            joined: campaign.candidate_count,
            completed: campaign.completed_count,
          })}
        </p>
      </div>

      {candidates.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border bg-card/50 p-10 text-center space-y-2">
          <Clock className="h-8 w-8 mx-auto text-muted-foreground" aria-hidden="true" />
          <p className="text-sm text-muted-foreground max-w-sm mx-auto">
            {t("campaigns.reportEmpty", {
              defaultValue: "No candidates yet. Share the invite link — results appear here as they come in.",
            })}
          </p>
        </div>
      ) : (
        <ol className="space-y-3">
          {candidates.map((row, idx) => (
            <CandidateRow key={row.professional_id} row={row} rank={idx + 1} locale={locale} />
          ))}
        </ol>
      )}
    </div>
  );
}

function CandidateRow({ row, rank, locale }: { row: CandidateReportRow; rank: number; locale: string }) {
  const { t } = useTranslation();
  const router = useRouter();
  const finished = row.assigned_sessions > 0 && row.completed_sessions === row.assigned_sessions;
  const tierStyle = row.badge_tier ? TIER_STYLES[row.badge_tier.toLowerCase()] : undefined;

  return (
    <li className="rounded-xl border border-border bg-card p-4">
      <div className="flex items-center gap-4">
        <span className="w-7 shrink-0 text-center text-sm font-bold text-muted-foreground">{rank}</span>

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="truncate text-sm font-semibold text-foreground">
              {row.display_name || row.username || t("campaigns.anonymous", { defaultValue: "Candidate" })}
            </p>
            {row.badge_tier && (
              <span
                className={cn(
                  "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium",
                  tierStyle ?? "bg-muted text-muted-foreground",
                )}
              >
                <Award className="h-3 w-3" aria-hidden="true" />
                {row.badge_tier}
              </span>
            )}
          </div>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {finished ? (
              <span className="inline-flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
                {t("campaigns.candidateFinished", { defaultValue: "All assessments completed" })}
              </span>
            ) : (
              t("campaigns.candidateProgress", {
                defaultValue: "{{done}} of {{total}} assessments completed",
                done: row.completed_sessions,
                total: row.assigned_sessions,
              })
            )}
          </p>
          {Object.keys(row.competency_scores).length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {Object.entries(row.competency_scores).map(([slug, score]) => (
                <span
                  key={slug}
                  className="rounded-full border border-border bg-muted/30 px-2 py-0.5 text-[10px] text-muted-foreground"
                >
                  {t(`competency.${slug}`, { defaultValue: slug.replace(/_/g, " ") })}: {Math.round(score)}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="flex shrink-0 flex-col items-end gap-1.5">
          {row.campaign_score != null && (
            <span className="text-lg font-bold text-foreground tabular-nums">
              {row.campaign_score.toFixed(1)}
            </span>
          )}
          {row.username && (
            <button
              onClick={() => router.push(`/${locale}/u/${row.username}`)}
              className="inline-flex items-center gap-1 text-xs text-primary underline-offset-4 hover:underline"
            >
              {t("campaigns.viewProfile", { defaultValue: "Profile" })}
              <ExternalLink className="h-3 w-3" aria-hidden="true" />
            </button>
          )}
        </div>
      </div>
    </li>
  );
}

/**
 * Paywall card — shown when the report endpoint returns 402 PAYMENT_REQUIRED
 * (org-billing flag on AND org lacks access). A value-forward upsell, not an error:
 * accent uses the `primary` token (purple), never error/destructive (red-adjacent).
 *
 * One primary CTA per screen (Constitution): "Unlock this report" (one-time) is the
 * filled button; "Subscribe" (recurring) is a low-emphasis ghost link. Both POST to
 * org-billing and redirect window.location to the returned Stripe checkout_url.
 *
 * The 402 detail's unlock_url / subscribe_url are dropped by apiFetch, but they are
 * deterministic constants, so we reconstruct them here from campaignId.
 */
function ReportPaywall({ campaignId, locale }: { campaignId: string; locale: string }) {
  const { t } = useTranslation();
  // "unlock" = one-time per-campaign; "subscribe" = recurring org plan.
  const [pending, setPending] = useState<"unlock" | "subscribe" | null>(null);
  const [checkoutError, setCheckoutError] = useState<string | null>(null);

  async function startCheckout(kind: "unlock" | "subscribe") {
    if (pending) return;
    setCheckoutError(null);
    setPending(kind);
    const url =
      kind === "unlock"
        ? `/api/org-billing/campaigns/${campaignId}/unlock`
        : "/api/org-billing/subscribe";
    try {
      // Empty body — org identity comes from the JWT apiFetch auto-injects.
      // Inline result type (no generated SDK dependency); both targets return { checkout_url }.
      const res = await apiFetch<{ checkout_url: string }>(url, { method: "POST" });
      if (res?.checkout_url) {
        window.location.href = res.checkout_url;
        return; // keep button disabled through the redirect
      }
      setCheckoutError(
        t("campaigns.unlockError", { defaultValue: "Could not start checkout — please try again." }),
      );
      setPending(null);
    } catch (err: unknown) {
      const status = (err as { status?: number })?.status;
      const code = (err as { code?: string })?.code;
      if (code === "ALREADY_HAS_ACCESS") {
        // Access was granted (e.g. another tab) — refresh to load the report.
        window.location.reload();
        return;
      }
      setCheckoutError(
        status === 503
          ? t("subscription.setupInProgress", {
              defaultValue: "Checkout setup in progress — contact us to unlock early.",
            })
          : t("campaigns.unlockError", { defaultValue: "Could not start checkout — please try again." }),
      );
      setPending(null);
    }
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-6 space-y-4">
      <Link
        href={`/${locale}/my-organization/campaigns`}
        className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
        {t("campaigns.backToList", { defaultValue: "Back to campaigns" })}
      </Link>

      <div className="rounded-xl border border-border bg-card p-8 text-center space-y-5">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-primary/10 text-primary">
          <Sparkles className="h-7 w-7" aria-hidden="true" />
        </div>

        <div className="space-y-2">
          <h1 className="text-2xl font-bold font-headline text-foreground">
            {t("campaigns.paywallTitle", { defaultValue: "Unlock this campaign's ranked report" })}
          </h1>
          <p className="mx-auto max-w-md text-sm text-muted-foreground">
            {t("campaigns.paywallBody", {
              defaultValue:
                "You've collected verified candidates. Unlock the ranked report to see who rises to the top.",
            })}
          </p>
        </div>

        <div className="space-y-3 pt-1">
          {/* Primary CTA — one-time unlock for this campaign */}
          <button
            type="button"
            onClick={() => startCheckout("unlock")}
            disabled={pending !== null}
            className="h-11 w-full max-w-xs mx-auto inline-flex items-center justify-center rounded-md bg-primary px-6 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {pending === "unlock"
              ? t("campaigns.redirecting", { defaultValue: "Opening checkout…" })
              : t("campaigns.paywallUnlockCta", { defaultValue: "Unlock this report" })}
          </button>

          {/* Secondary, low-emphasis — recurring subscription (one primary CTA per screen) */}
          <div>
            <button
              type="button"
              onClick={() => startCheckout("subscribe")}
              disabled={pending !== null}
              className="rounded-sm text-sm font-medium text-primary underline-offset-4 hover:underline outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {pending === "subscribe"
                ? t("campaigns.redirecting", { defaultValue: "Opening checkout…" })
                : t("campaigns.paywallSubscribeCta", {
                    defaultValue: "Or subscribe to unlock every report",
                  })}
            </button>
          </div>
        </div>

        {checkoutError && (
          <p className="text-xs text-muted-foreground" role="status">
            {checkoutError}
          </p>
        )}
      </div>
    </div>
  );
}
