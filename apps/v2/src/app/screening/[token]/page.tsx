import Link from "next/link";

/*
  v2 screening landing — server component, fetches the live campaign
  straight from the production API. The CTA bridges to the existing
  auth flow until v2 grows its own.
*/

interface PublicCampaign {
  title: string;
  description: string | null;
  org_name: string;
  org_logo_url: string | null;
  competency_slugs: string[];
  status: string;
  deadline_days: number;
  is_full: boolean;
}

const API = process.env.NEXT_PUBLIC_API_URL || "https://volauraapi-production.up.railway.app";
const LEGACY_APP = "https://volaura.app";

const COMPETENCY_NAMES: Record<string, string> = {
  communication: "Communication",
  reliability: "Reliability",
  english_proficiency: "English Proficiency",
  leadership: "Leadership",
  event_performance: "Event Performance",
  tech_literacy: "Tech Literacy",
  adaptability: "Adaptability",
  empathy_safeguarding: "Empathy & Safeguarding",
};

async function getCampaign(token: string): Promise<PublicCampaign | null> {
  try {
    const res = await fetch(`${API}/api/campaigns/public/${encodeURIComponent(token)}`, {
      next: { revalidate: 60 },
    });
    if (!res.ok) return null;
    return (await res.json()) as PublicCampaign;
  } catch {
    return null;
  }
}

export default async function ScreeningPage({ params }: { params: { token: string } }) {
  const campaign = await getCampaign(params.token);

  if (!campaign) {
    return (
      <main className="mx-auto flex min-h-screen max-w-xl flex-col justify-center px-6 py-16">
        <p className="font-display text-lg font-bold">
          VOLAURA<span className="text-seal">.</span>
        </p>
        <h1 className="mt-8 font-display text-3xl font-bold tracking-tight">
          This screening link isn&apos;t valid.
        </h1>
        <p className="mt-4 leading-relaxed text-ink-soft">
          It may have expired or been closed. Ask the organization that sent it
          for a fresh one — or explore VOLAURA from the start.
        </p>
        <Link href="/" className="mt-8 inline-block self-start bg-ink px-6 py-3 font-display text-sm font-semibold text-paper transition-colors hover:bg-seal">
          Go to VOLAURA
        </Link>
      </main>
    );
  }

  const open = campaign.status === "active" && !campaign.is_full;
  const joinUrl = `${LEGACY_APP}/en/screening/${params.token}`;

  return (
    <main className="mx-auto max-w-xl px-6 py-16">
      <p className="font-display text-lg font-bold">
        VOLAURA<span className="text-seal">.</span>
      </p>

      <div className="mt-10 border border-rule bg-paper-raised p-8 shadow-[6px_6px_0_0_var(--color-paper-sunken)]">
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-ink-faint">
          Screening by {campaign.org_name}
        </p>
        <h1 className="mt-3 font-display text-3xl font-bold leading-tight tracking-tight">
          {campaign.title}
        </h1>
        {campaign.description && (
          <p className="mt-4 leading-relaxed text-ink-soft">{campaign.description}</p>
        )}

        <div className="my-6 border-t border-rule" />

        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-ink-faint">
          You will be assessed on
        </p>
        <ul className="mt-3 flex flex-wrap gap-2">
          {campaign.competency_slugs.map((slug) => (
            <li
              key={slug}
              className="border border-rule bg-paper-sunken px-3 py-1 text-sm"
            >
              {COMPETENCY_NAMES[slug] ?? slug}
            </li>
          ))}
        </ul>

        {open ? (
          <a
            href={joinUrl}
            className="mt-8 block bg-ink px-6 py-3.5 text-center font-display text-sm font-semibold text-paper transition-colors hover:bg-seal"
          >
            Join this screening — free
          </a>
        ) : (
          <p className="mt-8 border border-rule bg-paper-sunken px-4 py-3 text-sm text-ink-soft">
            This screening is no longer accepting candidates.
          </p>
        )}
      </div>

      <p className="mt-6 text-sm leading-relaxed text-ink-soft">
        Free for candidates. Your verified AURA profile and scores stay yours
        forever — use them for every application after this one.
      </p>
    </main>
  );
}
