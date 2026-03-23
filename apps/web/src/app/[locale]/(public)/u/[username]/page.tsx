import { notFound } from "next/navigation";
import type { Metadata } from "next";
import Link from "next/link";
import { AuraRadarChart } from "@/components/aura/radar-chart";
import { ShareButtons } from "@/components/aura/share-buttons";
import initTranslations from "@/app/i18n";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface PublicProfile {
  id: string;
  username: string;
  display_name: string | null;
  avatar_url: string | null;
  bio: string | null;
  location: string | null;
  languages: string[];
  badge_issued_at: string | null;
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

async function fetchAura(volunteerId: string): Promise<AuraScore | null> {
  try {
    const r = await fetch(`${API_URL}/api/aura/${volunteerId}`, { next: { revalidate: 60 } });
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
    description: `${name}'s verified volunteer profile on Volaura. View their AURA score and competency breakdown.`,
    openGraph: {
      title: `${name} on Volaura`,
      description: profile.bio ?? `Verified volunteer profile`,
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
  platinum: "text-violet-400",
  gold: "text-yellow-400",
  silver: "text-slate-300",
  bronze: "text-amber-600",
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
    <main className="min-h-screen bg-background">
      {/* Header bar */}
      <div className="border-b border-border px-6 py-3 flex items-center justify-between">
        <Link href={`/${locale}`} className="font-bold text-lg">Volaura</Link>
        <Link
          href={`/${locale}/signup`}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          Get your AURA score
        </Link>
      </div>

      <div className="mx-auto max-w-2xl p-6 space-y-6">
        {/* Profile header */}
        <div className="flex items-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary text-xl font-bold text-primary-foreground">
            {name[0].toUpperCase()}
          </div>
          <div>
            <h1 className="text-2xl font-bold">{name}</h1>
            <p className="text-muted-foreground">@{profile.username}</p>
            {profile.location && (
              <p className="text-sm text-muted-foreground">{profile.location}</p>
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
            <div className="rounded-xl border border-border bg-card p-5 flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">{t("publicProfile.auraScore")}</p>
                <p className="text-4xl font-bold">{aura.overall_score.toFixed(1)}</p>
                <p className={`mt-1 text-sm font-semibold capitalize ${BADGE_COLORS[aura.badge_tier] ?? ""}`}>
                  {aura.badge_tier} {aura.elite_status && "· Elite ⭐"}
                </p>
              </div>
              <div className="w-40">
                <AuraRadarChart
                  competencyScores={aura.competency_scores}
                  badgeTier={aura.badge_tier}
                  size="sm"
                />
              </div>
            </div>

            <ShareButtons
              username={profile.username}
              overallScore={aura.overall_score}
              badgeTier={aura.badge_tier}
            />
          </>
        ) : (
          <div className="rounded-xl border border-border bg-card p-5 text-center text-muted-foreground">
            {t("publicProfile.auraNotAvailable")}
          </div>
        )}

        {/* CTA */}
        <div className="rounded-xl border border-primary/20 bg-primary/5 p-5 text-center space-y-3">
          <p className="font-semibold">{t("publicProfile.ctaTitle")}</p>
          <p className="text-sm text-muted-foreground">
            {t("publicProfile.ctaDescription")}
          </p>
          <Link
            href={`/${locale}/signup`}
            className="inline-block rounded-lg bg-primary px-6 py-2.5 font-medium text-primary-foreground hover:bg-primary/90"
          >
            Get started — it&apos;s free
          </Link>
        </div>
      </div>
    </main>
  );
}
