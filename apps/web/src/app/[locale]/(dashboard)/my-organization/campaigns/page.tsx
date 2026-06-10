"use client";

/**
 * Org screening campaigns — list, create, share invite link.
 *
 * B2B screening loop, org side: create a campaign (vacancy) -> share one link ->
 * candidates join and take assessments -> open the ranked report.
 * Decision: memory/decisions/2026-06-11-b2b-pivot.md
 */

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { ArrowRight, Check, Copy, Link2, Plus, Users } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils/cn";
import {
  useMyCampaigns,
  useCreateCampaign,
  useUpdateCampaignStatus,
  type Campaign,
} from "@/hooks/queries/use-campaigns";

const ALL_COMPETENCIES = [
  "communication",
  "reliability",
  "english_proficiency",
  "leadership",
  "event_performance",
  "tech_literacy",
  "adaptability",
  "empathy_safeguarding",
] as const;

export default function OrgCampaignsPage() {
  const { locale } = useParams<{ locale: string }>();
  const { t } = useTranslation();
  const { data: campaigns, isLoading, error } = useMyCampaigns();

  const [showForm, setShowForm] = useState(false);

  return (
    <div className="mx-auto w-full max-w-3xl space-y-6 px-4 py-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold font-headline text-foreground">
            {t("campaigns.title", { defaultValue: "Screening campaigns" })}
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {t("campaigns.subtitle", {
              defaultValue: "One link per vacancy. Candidates join, take assessments, you get a ranked report.",
            })}
          </p>
        </div>
        {!showForm && (
          <button
            onClick={() => setShowForm(true)}
            className="inline-flex shrink-0 items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground shadow-sm transition-all hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" aria-hidden="true" />
            {t("campaigns.newCta", { defaultValue: "New campaign" })}
          </button>
        )}
      </div>

      {showForm && <CreateCampaignForm onClose={() => setShowForm(false)} />}

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-28 w-full rounded-xl" />
          ))}
        </div>
      ) : error ? (
        <div className="rounded-xl border border-border bg-card p-6 text-center space-y-2">
          <p className="text-sm text-foreground">
            {error.status === 403
              ? t("campaigns.noOrg", {
                  defaultValue: "Create your organization profile first to run screening campaigns.",
                })
              : t("campaigns.loadError", {
                  defaultValue: "We couldn't load campaigns — please retry in a moment.",
                })}
          </p>
          {error.status === 403 && (
            <Link
              href={`/${locale}/my-organization`}
              className="inline-flex items-center gap-1 text-sm font-medium text-primary underline-offset-4 hover:underline"
            >
              {t("campaigns.goToOrg", { defaultValue: "Go to organization profile" })}
              <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
            </Link>
          )}
        </div>
      ) : !campaigns || campaigns.length === 0 ? (
        !showForm && (
          <div className="rounded-xl border border-dashed border-border bg-card/50 p-10 text-center space-y-3">
            <Users className="h-10 w-10 mx-auto text-muted-foreground" aria-hidden="true" />
            <p className="text-sm text-muted-foreground max-w-sm mx-auto">
              {t("campaigns.emptyState", {
                defaultValue:
                  "Your first campaign takes one minute: name the role, pick competencies, share the link.",
              })}
            </p>
          </div>
        )
      ) : (
        <div className="space-y-3">
          {campaigns.map((c) => (
            <CampaignCard key={c.id} campaign={c} locale={locale} />
          ))}
        </div>
      )}
    </div>
  );
}

function CreateCampaignForm({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  const createMutation = useCreateCampaign();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [slugs, setSlugs] = useState<string[]>(["communication", "reliability"]);
  const [deadlineDays, setDeadlineDays] = useState(14);
  const [formError, setFormError] = useState<string | null>(null);

  function toggleSlug(slug: string) {
    setSlugs((prev) => (prev.includes(slug) ? prev.filter((s) => s !== slug) : [...prev, slug]));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (title.trim().length < 3) {
      setFormError(t("campaigns.titleRequired", { defaultValue: "Give the campaign a name (3+ characters)." }));
      return;
    }
    if (slugs.length === 0) {
      setFormError(t("campaigns.competencyRequired", { defaultValue: "Pick at least one competency." }));
      return;
    }
    try {
      await createMutation.mutateAsync({
        title: title.trim(),
        description: description.trim() || undefined,
        competency_slugs: slugs,
        deadline_days: deadlineDays,
      });
      onClose();
    } catch {
      setFormError(
        t("campaigns.createError", { defaultValue: "Couldn't create the campaign — please try again." }),
      );
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-xl border border-border bg-card p-5 space-y-4">
      <div className="space-y-1.5">
        <label htmlFor="campaign-title" className="text-sm font-medium text-foreground">
          {t("campaigns.fieldTitle", { defaultValue: "Role / campaign name" })}
        </label>
        <input
          id="campaign-title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          maxLength={120}
          placeholder={t("campaigns.titlePlaceholder", { defaultValue: "e.g. Customer Support Specialist" })}
          className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>

      <div className="space-y-1.5">
        <label htmlFor="campaign-desc" className="text-sm font-medium text-foreground">
          {t("campaigns.fieldDescription", { defaultValue: "Description for candidates (optional)" })}
        </label>
        <textarea
          id="campaign-desc"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          maxLength={2000}
          rows={3}
          className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>

      <div className="space-y-2">
        <p className="text-sm font-medium text-foreground">
          {t("campaigns.fieldCompetencies", { defaultValue: "Competencies to assess" })}
        </p>
        <div className="flex flex-wrap gap-2">
          {ALL_COMPETENCIES.map((slug) => {
            const active = slugs.includes(slug);
            return (
              <button
                key={slug}
                type="button"
                aria-pressed={active}
                onClick={() => toggleSlug(slug)}
                className={cn(
                  "inline-flex items-center gap-1 rounded-full border px-3 py-1.5 text-xs transition-colors",
                  active
                    ? "border-primary bg-primary/10 text-foreground"
                    : "border-border bg-muted/30 text-muted-foreground hover:border-primary/50",
                )}
              >
                {active && <Check className="h-3 w-3 text-primary" aria-hidden="true" />}
                {t(`competency.${slug}`, { defaultValue: slug.replace(/_/g, " ") })}
              </button>
            );
          })}
        </div>
      </div>

      <div className="space-y-1.5">
        <label htmlFor="campaign-deadline" className="text-sm font-medium text-foreground">
          {t("campaigns.fieldDeadline", { defaultValue: "Days candidates have to finish" })}
        </label>
        <input
          id="campaign-deadline"
          type="number"
          min={1}
          max={60}
          value={deadlineDays}
          onChange={(e) => setDeadlineDays(Math.min(60, Math.max(1, Number(e.target.value) || 14)))}
          className="w-24 rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>

      {formError && <p className="text-sm text-[#D4B4FF]">{formError}</p>}

      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={createMutation.isPending}
          className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground shadow-sm transition-all hover:bg-primary/90 disabled:opacity-60"
        >
          {createMutation.isPending
            ? t("campaigns.creating", { defaultValue: "Creating..." })
            : t("campaigns.createCta", { defaultValue: "Create campaign" })}
        </button>
        <button
          type="button"
          onClick={onClose}
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          {t("common.cancel", { defaultValue: "Cancel" })}
        </button>
      </div>
    </form>
  );
}

function CampaignCard({ campaign, locale }: { campaign: Campaign; locale: string }) {
  const { t } = useTranslation();
  const router = useRouter();
  const updateStatus = useUpdateCampaignStatus();
  const [copied, setCopied] = useState(false);

  const inviteUrl =
    typeof window !== "undefined"
      ? `${window.location.origin}/${locale}/screening/${campaign.invite_token}`
      : "";

  async function copyLink(e: React.MouseEvent) {
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(inviteUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard unavailable — user can copy from the visible URL
    }
  }

  const isActive = campaign.status === "active";

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => router.push(`/${locale}/my-organization/campaigns/${campaign.id}`)}
      onKeyDown={(e) => {
        if (e.key === "Enter") router.push(`/${locale}/my-organization/campaigns/${campaign.id}`);
      }}
      className="rounded-xl border border-border bg-card p-5 space-y-3 cursor-pointer transition-colors hover:border-primary/40"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="text-base font-semibold text-foreground truncate">{campaign.title}</h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            {t("campaigns.cardMeta", {
              defaultValue: "{{joined}} joined · {{completed}} completed",
              joined: campaign.candidate_count,
              completed: campaign.completed_count,
            })}
          </p>
        </div>
        <span
          className={cn(
            "shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium",
            isActive ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground",
          )}
        >
          {t(`campaigns.status_${campaign.status}`, { defaultValue: campaign.status })}
        </span>
      </div>

      <div className="flex flex-wrap gap-1.5">
        {campaign.competency_slugs.map((slug) => (
          <span
            key={slug}
            className="rounded-full border border-border bg-muted/30 px-2 py-0.5 text-[10px] text-muted-foreground"
          >
            {t(`competency.${slug}`, { defaultValue: slug.replace(/_/g, " ") })}
          </span>
        ))}
      </div>

      <div className="flex items-center justify-between gap-3 pt-1">
        <div className="flex items-center gap-2 min-w-0">
          <Link2 className="h-3.5 w-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
          <span className="text-xs text-muted-foreground truncate font-mono">{inviteUrl}</span>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <button
            onClick={copyLink}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-accent"
          >
            {copied ? (
              <>
                <Check className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
                {t("campaigns.copied", { defaultValue: "Copied" })}
              </>
            ) : (
              <>
                <Copy className="h-3.5 w-3.5" aria-hidden="true" />
                {t("campaigns.copyLink", { defaultValue: "Copy link" })}
              </>
            )}
          </button>
          {isActive && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                updateStatus.mutate({ campaignId: campaign.id, status: "closed" });
              }}
              disabled={updateStatus.isPending}
              className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-accent disabled:opacity-60"
            >
              {t("campaigns.closeCta", { defaultValue: "Close" })}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
