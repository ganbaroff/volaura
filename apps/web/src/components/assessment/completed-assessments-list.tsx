"use client";

/**
 * D-5: Past results list on the assessment dashboard.
 *
 * Completed sessions are retained server-side forever, and the results page
 * replays them idempotently — but until this list there was no UI path back
 * to them. Feeds from GET /api/activity/me (type="assessment" items carry
 * the session id + competency slug) and deep-links each row to
 * /[locale]/assessment/[sessionId]/complete.
 *
 * Quiet by design: renders nothing while empty so new users see no clutter;
 * a load failure shows one muted line instead of blocking the start flow.
 */

import { useEffect, useState } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { ChevronRight, History } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { createClient } from "@/lib/supabase/client";
import { API_BASE } from "@/lib/api/client";

type ActivityItem = {
  id: string;
  type: string;
  created_at: string | null;
  metadata?: {
    competency_slug?: string | null;
  };
};

type CompletedAssessment = {
  sessionId: string;
  competencySlug: string | null;
  completedAt: string | null;
};

type LoadState = "loading" | "ready" | "error";

const MAX_VISIBLE = 10;

export function CompletedAssessmentsList({ locale }: { locale: string }) {
  const { t } = useTranslation();
  const [state, setState] = useState<LoadState>("loading");
  const [items, setItems] = useState<CompletedAssessment[]>([]);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const supabase = createClient();
        const {
          data: { session },
        } = await supabase.auth.getSession();
        const token = session?.access_token;
        if (!token) {
          // Not logged in — the page-level auth flow handles redirects; stay quiet.
          if (!cancelled) setState("ready");
          return;
        }

        const res = await fetch(`${API_BASE}/activity/me?limit=50`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const body = (await res.json()) as { data?: ActivityItem[] } | ActivityItem[];
        const feed = Array.isArray(body) ? body : (body.data ?? []);
        const completed = feed
          .filter((item) => item.type === "assessment")
          .slice(0, MAX_VISIBLE)
          .map((item) => ({
            sessionId: item.id,
            competencySlug: item.metadata?.competency_slug ?? null,
            completedAt: item.created_at,
          }));

        if (!cancelled) {
          setItems(completed);
          setState("ready");
        }
      } catch {
        if (!cancelled) setState("error");
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (state === "loading") {
    return (
      <div className="space-y-2" aria-hidden="true">
        <Skeleton className="h-4 w-40" />
        <Skeleton className="h-12 w-full rounded-xl" />
      </div>
    );
  }

  if (state === "error") {
    return (
      <p className="text-xs text-muted-foreground text-center">
        {t("assessment.pastResultsError", {
          defaultValue: "Couldn't load past results right now.",
        })}
      </p>
    );
  }

  if (items.length === 0) return null;

  const dateLocale = locale === "az" ? "az-Latn-AZ" : locale;

  return (
    <section className="space-y-2" aria-label={t("assessment.pastResults", { defaultValue: "Your completed assessments" })}>
      <div className="flex items-center gap-2">
        <History className="size-4 text-muted-foreground" aria-hidden="true" />
        <h2 className="text-sm font-semibold text-foreground">
          {t("assessment.pastResults", { defaultValue: "Your completed assessments" })}
        </h2>
      </div>
      <p className="text-xs text-muted-foreground">
        {t("assessment.pastResultsHint", {
          defaultValue: "Open any of them to revisit the result.",
        })}
      </p>
      <ul className="space-y-2">
        {items.map((item) => {
          const name = item.competencySlug
            ? t(`competency.${item.competencySlug}`, { defaultValue: item.competencySlug })
            : t("assessment.pastResultUnknownCompetency", { defaultValue: "Competency assessment" });
          const date = item.completedAt
            ? new Date(item.completedAt).toLocaleDateString(dateLocale, {
                day: "numeric",
                month: "short",
                year: "numeric",
              })
            : null;
          return (
            <li key={item.sessionId}>
              <Link
                href={`/${locale}/assessment/${item.sessionId}/complete`}
                className="flex items-center gap-3 rounded-2xl border border-border bg-surface-container-low px-4 py-3 transition-colors hover:border-primary/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary min-h-[44px]"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">{name}</p>
                  {date && <p className="text-xs text-muted-foreground">{date}</p>}
                </div>
                <span className="text-xs text-primary shrink-0">
                  {t("assessment.viewResult", { defaultValue: "View result" })}
                </span>
                <ChevronRight className="size-4 text-muted-foreground shrink-0" aria-hidden="true" />
              </Link>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
