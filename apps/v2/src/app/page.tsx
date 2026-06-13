import Link from "next/link";

/*
  VOLAURA v2 landing — B2B-first.
  The buyer is an employer drowning in unverifiable CVs.
  One promise, one primary CTA, a real-looking ranked report as proof.
*/

const COMPETENCIES = [
  ["Communication", "Writes and speaks so people act"],
  ["Reliability", "Shows up, follows through"],
  ["English", "CEFR-graded, behaviorally probed"],
  ["Leadership", "Moves a group without authority"],
  ["Event performance", "Delivers under live pressure"],
  ["Tech literacy", "Learns tools faster than you onboard"],
  ["Adaptability", "Re-plans when the plan dies"],
  ["Empathy & safeguarding", "Safe with clients and crowds"],
] as const;

const DEMO_ROWS = [
  { rank: 1, name: "L. Hasanova", score: 86.4, tier: "Gold", done: "3/3", note: "Strong written clarity; calm under simulated escalation." },
  { rank: 2, name: "R. Aliyev", score: 79.1, tier: "Gold", done: "3/3", note: "Fast learner profile; English B2 verified." },
  { rank: 3, name: "N. Mammadli", score: 71.8, tier: "Silver", done: "3/3", note: "Reliable pattern; leadership still developing." },
  { rank: 4, name: "S. Guliyeva", score: 64.0, tier: "Silver", done: "2/3", note: "Assessment in progress — one module remaining." },
] as const;

export default function Landing() {
  return (
    <main className="mx-auto max-w-5xl px-6">
      {/* ── Nav ─────────────────────────────────────────────────────────── */}
      <header className="flex items-baseline justify-between border-b border-rule py-5">
        <span className="font-display text-lg font-bold tracking-tight">
          VOLAURA<span className="text-seal">.</span>
        </span>
        <nav className="flex items-baseline gap-6 text-sm text-ink-soft">
          <a href="#how" className="hover:text-ink">How it works</a>
          <a href="#competencies" className="hover:text-ink">What we measure</a>
          <a href="#candidates" className="hover:text-ink">For candidates</a>
        </nav>
      </header>

      {/* ── Hero ────────────────────────────────────────────────────────── */}
      <section className="grid gap-10 py-20 md:grid-cols-[3fr_2fr] md:gap-16">
        <div>
          <p className="mb-5 inline-block border border-rule bg-paper-sunken px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-ink-soft">
            Verified candidate screening · Baku
          </p>
          <h1 className="font-display text-5xl font-bold leading-[1.04] tracking-tight md:text-6xl">
            Stop interviewing
            <br />
            blind<span className="text-seal">.</span>
          </h1>
          <p className="mt-6 max-w-md text-lg leading-relaxed text-ink-soft">
            Send every applicant one link. VOLAURA runs adaptive, AI-evaluated
            assessments and hands you a ranked shortlist of verified people —
            in 48 hours, not three weeks of interviews.
          </p>
          <div className="mt-9 flex items-center gap-5">
            <Link
              href="#how"
              className="rounded-xl bg-seal px-7 py-3.5 font-display text-sm font-semibold tracking-wide text-white transition-colors hover:bg-seal/90"
            >
              Create a screening campaign
            </Link>
            <a href="#candidates" className="text-sm text-ink-soft underline underline-offset-4 hover:text-ink">
              I&apos;m a candidate
            </a>
          </div>
        </div>

        {/* The seal — a verification certificate fragment */}
        <div className="relative hidden md:block">
          <div className="rounded-xl border border-rule bg-paper-raised p-6">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-ink-faint">Verified profile</p>
            <p className="mt-3 font-display text-xl font-bold">AURA 86.4</p>
            <p className="text-sm text-ink-soft">Gold tier · 8 competencies assessed</p>
            <div className="my-4 border-t border-rule" />
            <p className="text-sm leading-relaxed text-ink-soft">
              “Maintains clarity in escalated client scenarios; chose de-escalation
              over policy citation in 4 of 4 probes.”
            </p>
            <p className="mt-3 text-[11px] uppercase tracking-[0.18em] text-seal">— behavioral evidence, not a CV claim</p>
          </div>
        </div>
      </section>

      {/* ── How it works ─────────────────────────────────────────────────── */}
      <section id="how" className="border-t border-rule py-16">
        <h2 className="font-display text-2xl font-bold tracking-tight">Three steps. One link.</h2>
        <ol className="mt-8 grid gap-px border border-rule bg-rule md:grid-cols-3">
          {[
            ["01", "Create a campaign", "Name the role, pick the competencies that matter for it. One minute."],
            ["02", "Share one link", "Drop it in your job post, Telegram, anywhere. Every applicant goes through the same verified assessment."],
            ["03", "Read the ranked report", "Candidates arrive scored, tiered and evidenced. Interview the top five, skip the other ninety."],
          ].map(([n, title, body]) => (
            <li key={n} className="bg-paper-raised p-7">
              <span className="font-display text-sm font-bold text-seal">{n}</span>
              <h3 className="mt-3 font-display text-lg font-bold">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-ink-soft">{body}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* ── Report demo ──────────────────────────────────────────────────── */}
      <section className="border-t border-rule py-16">
        <div className="flex items-baseline justify-between">
          <h2 className="font-display text-2xl font-bold tracking-tight">The report you actually get</h2>
          <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-ink-faint">sample data</span>
        </div>
        <div className="mt-8 overflow-x-auto rounded-xl border border-rule bg-paper-raised">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead>
              <tr className="border-b border-rule text-[11px] uppercase tracking-[0.18em] text-ink-faint">
                <th className="px-5 py-3 font-semibold">#</th>
                <th className="px-5 py-3 font-semibold">Candidate</th>
                <th className="px-5 py-3 font-semibold">Score</th>
                <th className="px-5 py-3 font-semibold">Tier</th>
                <th className="px-5 py-3 font-semibold">Assessed</th>
                <th className="px-5 py-3 font-semibold">Behavioral evidence</th>
              </tr>
            </thead>
            <tbody>
              {DEMO_ROWS.map((r) => (
                <tr key={r.rank} className="border-b border-rule last:border-0">
                  <td className="px-5 py-4 font-display font-bold text-ink-faint">{r.rank}</td>
                  <td className="px-5 py-4 font-semibold">{r.name}</td>
                  <td className="px-5 py-4 font-display font-bold tabular-nums">{r.score.toFixed(1)}</td>
                  <td className="px-5 py-4">
                    <span className="border border-rule bg-paper-sunken px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide">
                      {r.tier}
                    </span>
                  </td>
                  <td className="px-5 py-4 tabular-nums text-ink-soft">{r.done}</td>
                  <td className="px-5 py-4 max-w-xs text-ink-soft">{r.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-4 text-sm text-ink-soft">
          Every score is earned in an adaptive assessment (the same math GRE uses),
          every sentence of evidence is generated from the candidate&apos;s actual answers.
        </p>
      </section>

      {/* ── Competencies ─────────────────────────────────────────────────── */}
      <section id="competencies" className="border-t border-rule py-16">
        <h2 className="font-display text-2xl font-bold tracking-tight">Eight things a CV can&apos;t prove</h2>
        <div className="mt-8 grid gap-px border border-rule bg-rule sm:grid-cols-2 md:grid-cols-4">
          {COMPETENCIES.map(([name, body]) => (
            <div key={name} className="bg-paper-raised p-6">
              <h3 className="font-display text-sm font-bold">{name}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-ink-soft">{body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Candidates strip ─────────────────────────────────────────────── */}
      <section id="candidates" className="border-t border-rule py-16">
        <div className="rounded-xl border border-rule bg-paper-sunken p-8 md:p-10">
          <h2 className="font-display text-2xl font-bold tracking-tight">Candidates pay nothing. Ever.</h2>
          <p className="mt-3 max-w-2xl leading-relaxed text-ink-soft">
            Take the assessment once — your verified AURA profile is yours forever.
            Use it for every application after this one. The next employer already
            trusts what the first one verified.
          </p>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────────── */}
      <footer className="flex items-baseline justify-between border-t border-rule py-10 text-sm text-ink-faint">
        <span>
          VOLAURA<span className="text-seal">.</span> — built in Baku, for the world.
        </span>
        <span>© 2026 Volaura Inc.</span>
      </footer>
    </main>
  );
}
