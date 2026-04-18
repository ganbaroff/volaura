"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import { TopBar } from "@/components/layout/top-bar";
import { Button } from "@/components/ui/button";
import { useFileGrievance, useOwnGrievances } from "@/hooks/queries/use-grievance";
import { CheckCircle2, ArrowLeft } from "lucide-react";
import { useEnergyMode } from "@/hooks/use-energy-mode";

const COMPETENCY_SLUGS = [
  "communication",
  "reliability",
  "english_proficiency",
  "leadership",
  "event_performance",
  "tech_literacy",
  "adaptability",
  "empathy_safeguarding",
];

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-amber-500/15 text-amber-700 dark:text-amber-300",
  reviewing: "bg-primary/15 text-primary",
  resolved: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300",
  rejected: "bg-muted text-muted-foreground",
};

export default function ContestScorePage() {
  const { t, i18n } = useTranslation();
  const locale = i18n.language;
  const router = useRouter();

  const { energy } = useEnergyMode();
  const isLow = energy === "low";

  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [competency, setCompetency] = useState<string>("");
  const [submitted, setSubmitted] = useState(false);

  const { mutate: fileGrievance, isPending, error } = useFileGrievance();
  const { data: ownGrievances } = useOwnGrievances();

  const canSubmit =
    subject.trim().length >= 3 &&
    subject.trim().length <= 200 &&
    description.trim().length >= 10 &&
    description.trim().length <= 5000 &&
    !isPending;

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    fileGrievance(
      {
        subject: subject.trim(),
        description: description.trim(),
        related_competency_slug: competency || null,
      },
      {
        onSuccess: () => {
          setSubmitted(true);
          setSubject("");
          setDescription("");
          setCompetency("");
        },
      }
    );
  };

  if (submitted) {
    return (
      <>
        <TopBar title={t("contest.title", { defaultValue: "Request a review" })} />
        <div className="mx-auto max-w-xl p-6 space-y-6">
          <div className="rounded-2xl border border-primary/30 bg-primary/5 p-6 flex items-start gap-4">
            <CheckCircle2 className="size-6 text-primary shrink-0 mt-0.5" aria-hidden="true" />
            <div className="space-y-2">
              <h2 className="text-lg font-semibold text-foreground">
                {t("contest.successTitle", { defaultValue: "We received your request." })}
              </h2>
              <p className="text-sm text-muted-foreground">
                {t("contest.successBody", {
                  defaultValue:
                    "A human reviewer will read your note and respond. You can track the status on this page.",
                })}
              </p>
            </div>
          </div>

          <div className="flex gap-3">
            <Button variant="outline" onClick={() => setSubmitted(false)}>
              {t("contest.fileAnother", { defaultValue: "File another" })}
            </Button>
            <Button asChild>
              <Link href={`/${locale}/aura`}>{t("contest.backToAura", { defaultValue: "Back to AURA" })}</Link>
            </Button>
          </div>

          {!isLow && ownGrievances && ownGrievances.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                {t("contest.historyTitle", { defaultValue: "Your requests" })}
              </h3>
              <ul className="space-y-2">
                {ownGrievances.map((g) => (
                  <li key={g.id} className="rounded-lg border border-border bg-card p-3">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-medium text-foreground truncate">{g.subject}</p>
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full font-medium shrink-0 ${STATUS_COLORS[g.status] ?? STATUS_COLORS.pending}`}
                      >
                        {t(`contest.status.${g.status}`, { defaultValue: g.status })}
                      </span>
                    </div>
                    {g.resolution && (
                      <p className="text-xs text-muted-foreground mt-2 whitespace-pre-line">
                        {g.resolution}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </>
    );
  }

  return (
    <>
      <TopBar title={t("contest.title", { defaultValue: "Request a review" })} />
      <div className="mx-auto max-w-xl p-6 space-y-6">
        <button
          type="button"
          onClick={() => router.push(`/${locale}/aura`)}
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="size-4" aria-hidden="true" />
          {t("common.back", { defaultValue: "Back" })}
        </button>

        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-foreground">
            {t("contest.heading", { defaultValue: "If your score does not feel right, tell us." })}
          </h1>
          <p className="text-sm text-muted-foreground">
            {t("contest.lede", {
              defaultValue:
                "A human reviews every request. We are not judging you — we are checking ourselves.",
            })}
          </p>
        </div>

        <form onSubmit={onSubmit} className="space-y-5">
          <div className="space-y-1.5">
            <label htmlFor="subject" className="block text-sm font-semibold text-foreground">
              {t("contest.subjectLabel", { defaultValue: "In one line, what happened?" })}
            </label>
            <input
              id="subject"
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              maxLength={200}
              minLength={3}
              required
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder={t("contest.subjectPlaceholder", { defaultValue: "Short summary" })}
            />
            <p className="text-xs text-muted-foreground">{subject.length}/200</p>
          </div>

          {!isLow && (
            <div className="space-y-1.5">
              <label htmlFor="competency" className="block text-sm font-semibold text-foreground">
                {t("contest.competencyLabel", { defaultValue: "Which competency (optional)?" })}
              </label>
              <select
                id="competency"
                value={competency}
                onChange={(e) => setCompetency(e.target.value)}
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="">{t("contest.competencyNone", { defaultValue: "— not specific —" })}</option>
                {COMPETENCY_SLUGS.map((slug) => (
                  <option key={slug} value={slug}>
                    {t(`competency.${slug}`, { defaultValue: slug })}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="space-y-1.5">
            <label htmlFor="description" className="block text-sm font-semibold text-foreground">
              {t("contest.descriptionLabel", { defaultValue: "Tell us what feels wrong." })}
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={6}
              maxLength={5000}
              minLength={10}
              required
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder={t("contest.descriptionPlaceholder", {
                defaultValue:
                  "Which question, which score, what you expected, why. The more specific, the better we can help.",
              })}
            />
            <p className="text-xs text-muted-foreground">{description.length}/5000</p>
          </div>

          {error && (
            <div className="rounded-lg border border-primary/30 bg-primary/5 p-3 text-sm text-foreground">
              {t("contest.errorGeneric", {
                defaultValue: "Could not send this request. Please try again in a moment.",
              })}
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <Button type="submit" disabled={!canSubmit} size="lg">
              {isPending
                ? t("contest.submitting", { defaultValue: "Sending…" })
                : t("contest.submit", { defaultValue: "Send for review" })}
            </Button>
            <Button variant="outline" asChild>
              <Link href={`/${locale}/aura`}>{t("common.cancel", { defaultValue: "Cancel" })}</Link>
            </Button>
          </div>
        </form>
      </div>
    </>
  );
}
