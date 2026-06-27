import Link from "next/link";

/*
  v2 screening invite landing — Direction C (ADHD-first) visual port.
  Server Component: fetches the live campaign from the production API
  (GET /api/campaigns/public/{token}). No API invented, backend unchanged.
  Visual reference: Manus prototype DirectionC.tsx (CInviteLanding).
  AZ default · no red · one primary CTA. Energy-mode interactivity is a
  later slice (shared client header); this slice ships the static landing.
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

// AZ labels for the 8 AURA competencies — content only, falls back to the slug.
const COMPETENCY_AZ: Record<string, string> = {
  communication: "Ünsiyyət",
  reliability: "Etibarlılıq",
  english_proficiency: "İngilis dili",
  leadership: "Liderlik",
  event_performance: "Tədbir Performansı",
  tech_literacy: "Texniki Savadlılıq",
  adaptability: "Uyğunlaşma",
  empathy_safeguarding: "Empatiya və Qayğı",
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

function Header() {
  return (
    <header className="sticky top-0 z-40 border-b border-rule/50 bg-paper/95 backdrop-blur">
      <div className="mx-auto flex max-w-[680px] items-center justify-between px-6 py-3.5">
        <div className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-[10px] bg-gradient-to-br from-seal to-[#a78bfa] text-white">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 3v18M3 12h18" />
            </svg>
          </span>
          <span className="font-display text-base font-bold tracking-tight">VOLAURA</span>
        </div>
        <div className="flex items-center gap-3 text-xs font-medium">
          <span className="text-ink-faint">Tam rejim</span>
          <span className="text-ink-soft">AZ</span>
        </div>
      </div>
    </header>
  );
}

export default async function ScreeningPage({ params }: { params: { token: string } }) {
  const campaign = await getCampaign(params.token);

  if (!campaign) {
    return (
      <div className="min-h-screen bg-paper text-ink">
        <Header />
        <main className="mx-auto max-w-[640px] px-6 py-16">
          <h1 className="font-display text-3xl font-bold tracking-tight">Bu link etibarlı deyil</h1>
          <p className="mt-4 leading-relaxed text-ink-soft">
            Link vaxtı keçmiş və ya bağlanmış ola bilər. Sizə göndərən təşkilatdan yenisini istəyin.
          </p>
          <Link
            href="/"
            className="mt-8 inline-block rounded-xl bg-seal px-6 py-3 font-display text-sm font-semibold text-white transition-colors hover:bg-seal/90"
          >
            VOLAURA-ya keç
          </Link>
        </main>
      </div>
    );
  }

  const open = campaign.status === "active" && !campaign.is_full;
  const orgInitial = campaign.org_name?.[0]?.toUpperCase() ?? "V";

  return (
    <div className="min-h-screen bg-paper text-ink">
      <Header />
      <main className="mx-auto max-w-[640px] px-6 pb-20 pt-12">
        {/* Organisation context */}
        <div className="mb-8 flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-[10px] border border-seal/20 bg-seal-soft/50 text-sm font-bold text-seal">
            {orgInitial}
          </span>
          <div>
            <div className="text-[13px] font-medium text-ink-faint">{campaign.org_name}</div>
            <div className="text-xs text-ink-faint">{campaign.deadline_days} gün qalıb</div>
          </div>
        </div>

        {/* Role title */}
        <h1 className="mb-4 font-display text-[clamp(28px,5vw,40px)] font-bold leading-tight tracking-tight">
          {campaign.title}
        </h1>
        {campaign.description && (
          <p className="mb-10 text-base leading-relaxed text-ink-soft">{campaign.description}</p>
        )}

        {/* Competencies */}
        <div className="mb-10">
          <div className="mb-3 text-xs font-semibold uppercase tracking-[0.08em] text-ink-faint">
            Qiymətləndirilən Bacarıqlar
          </div>
          <div className="flex flex-wrap gap-2">
            {campaign.competency_slugs.map((slug) => (
              <span
                key={slug}
                className="rounded-full border border-seal/20 bg-seal-soft/50 px-3.5 py-1.5 text-[13px] font-medium text-[#c4b5fd]"
              >
                {COMPETENCY_AZ[slug] ?? slug.replace(/_/g, " ")}
              </span>
            ))}
          </div>
        </div>

        {/* Trust card — decision-support, not a verdict */}
        <div className="mb-10 flex gap-3.5 rounded-[14px] border border-rule bg-paper-raised p-5">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[10px] bg-seal-soft/50 text-seal">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2 4 6v6c0 5 3.5 7.5 8 10 4.5-2.5 8-5 8-10V6z" />
            </svg>
          </span>
          <div>
            <div className="mb-1 text-sm font-semibold">Ədalətli və şəffaf</div>
            <p className="text-[13px] leading-relaxed text-ink-soft">
              Qiymətləndirmə nəticəsi qərar dəstəyidir — avtomatik işə qəbul qərarı deyil. Son qərar
              insana aiddir, və insan yoxlaması mövcuddur.
            </p>
          </div>
        </div>

        {/* Single primary CTA */}
        {open ? (
          <Link
            href={`/screening/${encodeURIComponent(params.token)}/run`}
            className="flex w-full items-center justify-center gap-2 rounded-[14px] bg-seal px-8 py-[18px] font-display text-base font-bold tracking-tight text-white transition-shadow hover:shadow-[0_0_32px_rgba(124,92,252,0.35)]"
          >
            Başla
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="m9 18 6-6-6-6" />
            </svg>
          </Link>
        ) : (
          <div className="rounded-[14px] border border-rule bg-paper-sunken px-5 py-4 text-sm text-ink-soft">
            Bu skrininq artıq namizəd qəbul etmir.
          </div>
        )}

        {open && (
          <p className="mt-4 text-center text-[13px] text-ink-faint">İstənilən vaxt dayandıra bilərsiniz</p>
        )}
      </main>
    </div>
  );
}
