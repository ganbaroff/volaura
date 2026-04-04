import { notFound } from "next/navigation";
import type { Metadata } from "next";
import Link from "next/link";
import { ShieldCheck, Award, Clock, BarChart3 } from "lucide-react";
import initTranslations from "@/app/i18n";
import { API_BASE } from "@/lib/api/client";

interface Props {
  params: Promise<{ locale: string; username: string; sessionId: string }>;
}

interface VerificationData {
  verified: boolean;
  platform: string;
  session_id: string;
  competency_slug: string;
  competency_name: string | null;
  competency_score: number;
  badge_tier: string;
  questions_answered: number;
  completed_at: string | null;
  display_name: string | null;
  username: string | null;
}

const BADGE_COLORS: Record<string, string> = {
  platinum: "text-violet-400 border-violet-400/30",
  gold: "text-yellow-400 border-yellow-400/30",
  silver: "text-slate-300 border-slate-300/30",
  bronze: "text-amber-600 border-amber-600/30",
  none: "text-muted-foreground border-border",
};

const BADGE_BG: Record<string, string> = {
  platinum: "bg-violet-400/10",
  gold: "bg-yellow-400/10",
  silver: "bg-slate-300/10",
  bronze: "bg-amber-600/10",
  none: "bg-muted/10",
};

async function fetchVerification(sessionId: string): Promise<VerificationData | null> {
  try {
    const res = await fetch(`${API_BASE}/assessment/verify/${sessionId}`, {
      next: { revalidate: 3600 },
    });
    if (!res.ok) return null;
    const json = await res.json();
    return json.data ?? json;
  } catch {
    return null;
  }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { username, sessionId } = await params;
  const data = await fetchVerification(sessionId);
  if (!data) return { title: "Verification not found — Volaura" };

  const name = data.display_name ?? username;
  const comp = data.competency_name ?? data.competency_slug;
  return {
    title: `${name} — ${comp} ${data.competency_score}/100 — Volaura Verified`,
    description: `${name} scored ${data.competency_score}/100 in ${comp} on Volaura. This result is verified by adaptive IRT assessment.`,
    openGraph: {
      title: `${name} — Verified ${comp} Score`,
      description: `Score: ${data.competency_score}/100 | Badge: ${data.badge_tier} | ${data.questions_answered} questions answered`,
    },
  };
}

export default async function VerificationPage({ params }: Props) {
  const { locale, username, sessionId } = await params;
  const { t } = await initTranslations(locale, ["common"]);
  const data = await fetchVerification(sessionId);

  if (!data) notFound();

  const name = data.display_name ?? username;
  const comp = data.competency_name ?? data.competency_slug;
  const tier = data.badge_tier ?? "none";
  const colorClass = BADGE_COLORS[tier] ?? BADGE_COLORS.none;
  const bgClass = BADGE_BG[tier] ?? BADGE_BG.none;
  const completedDate = data.completed_at
    ? new Date(data.completed_at).toLocaleDateString(locale === "az" ? "az-AZ" : "en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    : null;

  return (
    <main className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <div className="border-b border-border px-4 py-3 flex items-center justify-between">
        <Link href={`/${locale}`} className="font-bold text-lg">Volaura</Link>
        <div className="flex items-center gap-1.5 text-emerald-400 text-sm font-medium">
          <ShieldCheck className="h-4 w-4" />
          <span>{t("verification.verified", { defaultValue: "Verified" })}</span>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex items-center justify-center p-4">
        <div className={`max-w-md w-full rounded-2xl border ${colorClass} ${bgClass} p-6 space-y-6`}>
          {/* User + Badge */}
          <div className="text-center space-y-2">
            <div className={`inline-flex items-center gap-2 text-sm font-medium ${colorClass}`}>
              <Award className="h-5 w-5" />
              <span className="uppercase tracking-wider">{tier}</span>
            </div>
            <h1 className="text-2xl font-bold text-foreground">{name}</h1>
            <p className="text-muted-foreground text-sm">
              {t("verification.assessedBy", { defaultValue: "Assessed by Volaura adaptive testing" })}
            </p>
          </div>

          {/* Score */}
          <div className="text-center">
            <div className={`text-5xl font-bold ${colorClass}`}>
              {data.competency_score}
            </div>
            <div className="text-muted-foreground text-sm mt-1">{comp}</div>
          </div>

          {/* Details */}
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-lg bg-surface-container p-3 text-center">
              <BarChart3 className="h-4 w-4 mx-auto mb-1 text-muted-foreground" />
              <div className="text-sm font-medium">{data.questions_answered}</div>
              <div className="text-xs text-muted-foreground">
                {t("verification.questions", { defaultValue: "Questions" })}
              </div>
            </div>
            <div className="rounded-lg bg-surface-container p-3 text-center">
              <Clock className="h-4 w-4 mx-auto mb-1 text-muted-foreground" />
              <div className="text-sm font-medium">{completedDate ?? "—"}</div>
              <div className="text-xs text-muted-foreground">
                {t("verification.completed", { defaultValue: "Completed" })}
              </div>
            </div>
          </div>

          {/* How it works */}
          <div className="rounded-lg bg-surface-dim p-4 space-y-2">
            <h3 className="text-sm font-medium text-foreground">
              {t("verification.howTitle", { defaultValue: "How this score was verified" })}
            </h3>
            <ul className="text-xs text-muted-foreground space-y-1">
              <li>{t("verification.how1", { defaultValue: "Adaptive IRT assessment adjusts difficulty to each user" })}</li>
              <li>{t("verification.how2", { defaultValue: "Anti-gaming system detects suspicious patterns" })}</li>
              <li>{t("verification.how3", { defaultValue: "AI evaluation cross-checks open-ended responses" })}</li>
              <li>{t("verification.how4", { defaultValue: "Score is weighted across 8 professional competencies" })}</li>
            </ul>
          </div>

          {/* CTA */}
          <div className="text-center">
            <Link
              href={`/${locale}/u/${username}`}
              className="text-sm text-primary hover:underline"
            >
              {t("verification.viewProfile", { defaultValue: "View full profile" })} &rarr;
            </Link>
          </div>

          {/* Footer */}
          <div className="text-center text-xs text-muted-foreground pt-2 border-t border-border">
            {t("verification.footer", { defaultValue: "This assessment was conducted on the Volaura platform using internationally recognized psychometric standards (IRT 3PL)." })}
          </div>
        </div>
      </div>
    </main>
  );
}
