import { notFound } from "next/navigation";
import type { Metadata } from "next";
import Link from "next/link";
import { Clock } from "lucide-react";
import { AuraRadarChart } from "@/components/aura/radar-chart";
import { ShareButtons } from "@/components/aura/share-buttons";
import { IntroRequestButton } from "@/components/profile/intro-request-button";
import { ProfileViewTracker } from "@/components/profile/profile-view-tracker";
import { ChallengeButton } from "@/components/profile/challenge-button";
import initTranslations from "@/app/i18n";
import { API_BASE } from "@/lib/api/client";
import { getAchievementLevelKey } from "@/lib/utils/achievement-level";

const API_URL = API_BASE;

interface PublicProfile {
  id: string;
  username: string;
  display_name: string | null;
  avatar_url: string | null;
  bio: string | null;
  location: string | null;
  languages: string[];
  badge_issued_at: string | null;
  registration_number: number | null;
  registration_tier: string | null;
  percentile_rank: number | null;
}

interface AuraScore {
  overall_score: number;
  badge_tier: string;
  elite_status: boolean;
  competency_scores: Record<string, number>;
}

async function fetchProfile(username: string): Promise<PublicProfile | null> {
  try {
    const r = await fetch(`${API_URL}/api/profiles/${username}`, { next: { revalidate: 60 } });
    return r.ok ? r.json() : null;
  } catch {
    return null;
  }
}

async function fetchAura(userId: string): Promise<AuraScore | null> {
  try {
    const r = await fetch(`${API_URL}/api/aura/${userId}`, { next: { revalidate: 60 } });
    return r.ok ? r.json() : null;
  } catch {
    return null;
  }
}

interface Props {
  params: Promise<{ locale: string; username: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { username } = await params;
  const profile = await fetchProfile(username);
  if (!profile) return { title: "Profile not found — Volaura" };

  const name = profile.display_name ?? profile.username;
  return {
    title: `${name} — Volaura`,
    description: `${name}'s verified professional profile on Volaura. View their AURA score and competency breakdown.`,
    openGraph: {
      title: `${name} on Volaura`,
      description: profile.bio ?? `Verified professional profile`,
      images: [`/u/${username}/card`],
    },
    twitter: {
      card: "summary_large_image",
      title: `${name} on Volaura`,
      images: [`/u/${username}/card`],
    },
  };
}

const BADGE_COLORS: Record<string, string> = {
  platinum: "text-aura-platinum",
  gold: "text-aura-gold",
  silver: "text-aura-silver",
  bronze: "text-aura-bronze",
  none: "text-muted-foreground",
};

export default async function PublicProfilePage({ params }: Props) {
  const { locale, username } = await params;
  const { t } = await initTranslations(locale, ["common"]);
  const profile = await fetchProfile(username);
  if (!profile) notFound();

  const aura = await fetchAura(profile.id);
  const name = profile.display_name ?? profile.username;

  return (
    <main className="min-h-screen bg-background mesh-gradient-hero">
      <ProfileViewTracker username={username} />
      {/* Header bar — liquid glass */}
      <div className="glass-header border-b border-border/50 px-4 py-3 flex items-center justify-between gap-2 sticky top-0" style={{ zIndex: "var(--z-sticky)" } as React.CSSProperties}>
        <Link href={`/${locale}`} className="font-headline font-bold text-lg shrink-0 text-primary">Volaura</Link>
        <Link
          href={`/${locale}/signup`}
          className="btn-primary-gradient rounded-xl px-4 py-2.5 min-h-[44px] flex items-center text-sm font-semibold energy-target"
        >
          {t("publicProfile.getAuraScore")}
        </Link>
      </div>

      <div className="mx-auto max-w-2xl px-4 py-6 space-y-6">
        {/* Profile header */}
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-primary/15 text-xl font-bold text-primary ring-2 ring-primary/20">
            {name[0].toUpperCase()}
          </div>
          <div className="min-w-0">
            <h1 className="text-xl font-headline font-bold truncate">{name}</h1>
            <p className="text-muted-foreground">@{profile.username}</p>
            {profile.location && (
              <p className="text-sm text-muted-foreground">{profile.location}</p>
            )}
            {profile.registration_number && (
              <p className="text-xs font-mono text-muted-foreground mt-0.5">
                {profile.registration_tier === "founding_100" ? "⭐ " : ""}
                #{String(profile.registration_number).padStart(4, "0")}
                {profile.registration_tier === "founding_100"
                  ? ` · ${t("profile.foundingMember")}`
                  : profile.registration_tier === "founding_1000"
                  ? ` · ${t("profile.founding1000")}`
                  : ""}
              </p>
            )}
          </div>
        </div>

        {profile.bio && (
          <p className="text-sm text-foreground">{profile.bio}</p>
        )}

        {profile.languages.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {profile.languages.map((lang) => (
              <span key={lang} className="rounded-full border border-border px-2.5 py-0.5 text-xs font-medium uppercase">
                {lang}
              </span>
            ))}
          </div>
        )}

        {/* AURA section */}
        {aura ? (
          <>
            <div className="liquid-glass p-4 sm:p-5">
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm text-muted-foreground">{t("publicProfile.auraScore")}</p>
                  <p className="text-3xl sm:text-4xl font-bold">{aura.overall_score.toFixed(1)}</p>
                  <p className={`mt-1 text-sm font-semibold capitalize ${BADGE_COLORS[aura.badge_tier] ?? ""}`}>
                    {aura.badge_tier} {aura.elite_status && "· Elite ⭐"}
                  </p>
                  {profile.percentile_rank !== null && profile.percentile_rank !== undefined && (
                    <p className="mt-1.5 text-xs font-medium text-primary">
                      {/* CIS-001: Achievement level replaces "Top X%" — non-competitive framing for AZ/CIS users */}
                      {t(getAchievementLevelKey(profile.percentile_rank))}
                    </p>
                  )}
                </div>
                <div className="w-32 sm:w-40 shrink-0">
                  <AuraRadarChart
                    competencyScores={aura.competency_scores}
                    badgeTier={aura.badge_tier}
                    size="sm"
                  />
                </div>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <ShareButtons
                username={profile.username}
                overallScore={aura.overall_score}
                badgeTier={aura.badge_tier}
              />
              <ChallengeButton username={profile.username} />
            </div>
          </>
        ) : (
          <div className="liquid-glass p-5 text-center space-y-2">
            <Clock className="mx-auto h-5 w-5 text-muted-foreground" aria-hidden="true" />
            <p className="text-sm font-medium">{t("publicProfile.assessmentInProgress")}</p>
            <p className="text-sm text-muted-foreground">{t("publicProfile.assessmentInProgressDesc")}</p>
          </div>
        )}

        {/* Org-only: Request Introduction */}
        <IntroRequestButton professionalId={profile.id} professionalName={name} />

        {/* CTA */}
        <div className="liquid-glass p-5 text-center space-y-3">
          <p className="font-headline font-semibold">{t("publicProfile.ctaTitle")}</p>
          <p className="text-sm text-muted-foreground">
            {t("publicProfile.ctaDescription")}
          </p>
          <Link
            href={`/${locale}/signup`}
            className="inline-block btn-primary-gradient rounded-xl px-6 py-2.5 font-semibold energy-target"
          >
            {t("publicProfile.getStarted")}
          </Link>
        </div>
      </div>
    </main>
  );
}
