import type { ReactNode } from "react";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import Link from "next/link";
import { Building2, Calendar, Globe } from "lucide-react";
import initTranslations from "@/app/i18n";
import { API_BASE } from "@/lib/api/client";

const API_URL = API_BASE;

// ── Types ──────────────────────────────────────────────────────────────────────

interface OrgDetail {
  id: string;
  name: string;
  description: string | null;
  website: string | null;
  is_verified: boolean;
  trust_score: number | null;
  events_count?: number;
  created_at: string;
}

// ── Data fetching ──────────────────────────────────────────────────────────────

async function fetchOrg(id: string): Promise<OrgDetail | null> {
  try {
    const r = await fetch(`${API_URL}/api/organizations/${id}`, {
      next: { revalidate: 60 },
    });
    if (r.status === 404) return null;
    if (!r.ok) return null;
    return r.json();
  } catch {
    return null;
  }
}

// ── Metadata ──────────────────────────────────────────────────────────────────

interface Props {
  params: Promise<{ locale: string; id: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const org = await fetchOrg(id);
  if (!org) return { title: "Organization not found — Volaura" };

  return {
    title: `${org.name} — Volaura`,
    description:
      org.description ??
      `${org.name} is a verified partner organization on Volaura. Browse their events and volunteer opportunities.`,
    openGraph: {
      title: `${org.name} on Volaura`,
      description: org.description ?? `Partner organization on Volaura`,
    },
  };
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default async function OrgDetailPage({ params }: Props) {
  const { locale, id } = await params;
  const { t } = await initTranslations(locale, ["common"]);

  const org = await fetchOrg(id);
  if (!org) notFound();

  const initial = org.name.trim()[0]?.toUpperCase() ?? "O";

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Back nav */}
      <div className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 py-4">
          <Link
            href={`/${locale}/organizations`}
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            ← {t("orgs.discoveryTitle")}
          </Link>
        </div>
      </div>

      {/* Content */}
      <main className="max-w-3xl mx-auto px-4 py-10 space-y-8">

        {/* Org header */}
        <div className="flex items-start gap-5">
          {/* Avatar */}
          <div className="size-16 rounded-2xl bg-primary/10 flex items-center justify-center shrink-0">
            <span className="text-2xl font-bold text-primary">{initial}</span>
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-2xl font-bold text-foreground">{org.name}</h1>
              {org.is_verified && (
                <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2.5 py-1 text-xs font-semibold text-primary">
                  ✓ {t("orgs.verified")}
                </span>
              )}
            </div>

            {org.website && (
              <a
                href={org.website}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-primary transition-colors mt-1"
              >
                <Globe className="size-3.5" aria-hidden="true" />
                {org.website.replace(/^https?:\/\//, "")}
              </a>
            )}
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
          <StatCard
            icon={<Calendar className="size-4 text-primary" aria-hidden="true" />}
            label={t("orgs.totalEvents")}
            value={String(org.events_count ?? 0)}
          />
          {org.trust_score != null && (
            <StatCard
              icon={<Building2 className="size-4 text-primary" aria-hidden="true" />}
              label={t("orgs.trustScore")}
              value={`${Math.round(org.trust_score * 100)}%`}
            />
          )}
        </div>

        {/* Description */}
        {org.description && (
          <section className="rounded-xl border border-border bg-card p-5 space-y-2">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
              {t("orgs.aboutSection")}
            </h2>
            <p className="text-sm text-foreground leading-relaxed">{org.description}</p>
          </section>
        )}

        {/* CTA */}
        <section className="rounded-xl border border-border bg-card p-6 text-center space-y-4">
          <h2 className="text-lg font-bold text-foreground">{t("orgs.ctaTitle")}</h2>
          <p className="text-sm text-muted-foreground">{t("orgs.ctaSubtitle")}</p>
          <Link
            href={`/${locale}/login`}
            className="inline-flex items-center gap-2 rounded-full bg-primary px-6 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            {t("orgs.volunteerCta")}
          </Link>
        </section>

      </main>
    </div>
  );
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function StatCard({
  icon,
  label,
  value,
}: {
  icon: ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-4 flex flex-col items-center gap-1 text-center">
      <div className="size-8 rounded-full bg-primary/10 flex items-center justify-center">
        {icon}
      </div>
      <p className="text-xl font-bold text-foreground">{value}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  );
}
