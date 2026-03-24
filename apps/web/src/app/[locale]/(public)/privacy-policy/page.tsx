"use client";

import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function PrivacyPolicyPage() {
  const params = useParams();
  const locale = (params?.locale as string) || "en";

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <div className="border-b border-white/10 bg-surface-container/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center gap-4">
          <Link
            href={`/${locale}`}
            className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Volaura
          </Link>
        </div>
      </div>

      {/* Content */}
      <main className="max-w-3xl mx-auto px-4 py-12">
        <div className="mb-10">
          <h1 className="text-3xl font-bold mb-2">Privacy Policy</h1>
          <p className="text-muted-foreground text-sm">
            Effective date: April 1, 2026 &nbsp;·&nbsp; Last updated: March 24, 2026 &nbsp;·&nbsp; Version 1.0
          </p>
        </div>

        <div className="space-y-10 text-sm leading-relaxed">

          <Section title="1. Who We Are">
            <p>
              Volaura is a verified competency platform for volunteers, operated in Azerbaijan.
              We help volunteers prove their skills and help organizations find verified talent.
            </p>
            <p className="text-muted-foreground mt-2">
              Contact:{" "}
              <a href="mailto:privacy@volaura.az" className="text-primary underline">
                privacy@volaura.az
              </a>
            </p>
          </Section>

          <Section title="2. What Data We Collect">
            <h3 className="font-medium text-foreground mb-2">Data you provide</h3>
            <PolicyTable
              headers={["Data", "Why We Collect It", "Legal Basis"]}
              rows={[
                ["Name, email, username", "Account creation and identity", "Contract (GDPR Art. 6(1)(b))"],
                ["Password (hashed)", "Authentication", "Contract"],
                ["Location (city/region)", "Matching volunteers to local opportunities", "Legitimate interest"],
                ["Languages spoken", "Matching quality", "Legitimate interest"],
                ["Assessment answers", "Computing your AURA score", "Contract"],
                ["Bio / self-description", "Profile completeness, org matching", "Contract"],
              ]}
            />

            <h3 className="font-medium text-foreground mt-4 mb-2">Data we compute</h3>
            <PolicyTable
              headers={["Data", "Description"]}
              rows={[
                ["AURA Score (0–100)", "Weighted competency score across 8 dimensions"],
                ["Badge tier", "Derived from AURA score (Bronze / Silver / Gold / Platinum)"],
                ["Theta (IRT ability)", "Internal assessment calibration — never shown to organizations"],
                ["Anti-gaming signals", "Timing patterns to detect spoofed responses — quality use only"],
                ["Competency embeddings", "768-dim vector for semantic volunteer search — not identifiable alone"],
              ]}
            />

            <h3 className="font-medium text-foreground mt-4 mb-2">Data we do NOT collect</h3>
            <ul className="list-disc list-inside space-y-1 text-muted-foreground">
              <li>Payment card details (no payment processing in v1)</li>
              <li>Government IDs or passports</li>
              <li>Biometric data</li>
              <li>Location tracking / GPS</li>
              <li>Contacts or social graph</li>
            </ul>
          </Section>

          <Section title="3. How We Use Your Data">
            <ol className="list-decimal list-inside space-y-2 text-muted-foreground">
              <li><strong className="text-foreground">Deliver the service</strong> — run assessments, compute AURA scores, issue badges</li>
              <li><strong className="text-foreground">Volunteer–organization matching</strong> — orgs search by competency, location, languages</li>
              <li><strong className="text-foreground">Platform improvement</strong> — aggregate analytics (non-identifiable) to improve IRT calibration</li>
              <li><strong className="text-foreground">Security</strong> — rate limiting, anti-fraud, preventing score manipulation</li>
              <li><strong className="text-foreground">Communications</strong> — assessment results, badge notifications (opt-in)</li>
            </ol>
            <p className="text-muted-foreground mt-3">
              We do <strong className="text-foreground">not</strong> sell your data, use it for advertising, share raw answers with organizations,
              or use your profile outside Volaura without explicit consent.
            </p>
          </Section>

          <Section title="4. Who Can See Your Data">
            <PolicyTable
              headers={["Party", "What They See", "Conditions"]}
              rows={[
                ["You", "Everything about yourself", "Always"],
                ["Organizations (verified)", "Username, AURA score, badge tier, location, languages", "Only if you have a public profile"],
                ["Volaura team", "All data for support/security", "Role-based access, logged"],
                ["Supabase (infrastructure)", "All stored data", "Data Processing Agreement in place"],
                ["Google (Gemini API)", "Assessment answers sent for evaluation", "Gemini Enterprise DPA — no training on your data"],
                ["Railway / Vercel (hosting)", "API and frontend request logs", "SOC 2 compliant"],
              ]}
            />
          </Section>

          <Section title="5. Your Rights (GDPR + Local Law)">
            <div className="space-y-2 text-muted-foreground">
              {[
                ["Access", "Request a copy of all data we hold about you"],
                ["Rectification", "Correct inaccurate data"],
                ["Erasure", "Delete your account and all associated data"],
                ["Portability", "Export your AURA history and badges in JSON format"],
                ["Objection", "Object to processing based on legitimate interest"],
                ["Restrict", "Limit how we process your data while a dispute is resolved"],
                ["Withdraw consent", "For any processing based on consent"],
              ].map(([right, desc]) => (
                <div key={right} className="flex gap-3">
                  <span className="font-medium text-foreground min-w-[130px]">{right}</span>
                  <span>{desc}</span>
                </div>
              ))}
            </div>
            <p className="text-muted-foreground mt-4">
              Email{" "}
              <a href="mailto:privacy@volaura.az" className="text-primary underline">privacy@volaura.az</a>{" "}
              with subject <em>&quot;Data Rights Request — [your username]&quot;</em>. We respond within 30 days.
            </p>
          </Section>

          <Section title="6. Data Retention">
            <PolicyTable
              headers={["Data type", "Retention", "Why"]}
              rows={[
                ["Active account data", "Until account deletion", "Service delivery"],
                ["Assessment sessions", "2 years after completion", "Score recalibration, disputes"],
                ["AURA score history", "3 years", "Longitudinal competency tracking"],
                ["Deleted account data", "30 days (soft delete)", "Recovery window"],
                ["Security logs", "90 days", "Incident investigation"],
                ["Anonymized analytics", "Indefinite", "Platform improvement"],
              ]}
            />
            <p className="text-muted-foreground mt-3">
              When you delete your account, all personally identifiable data is permanently erased within 30 days.
            </p>
          </Section>

          <Section title="7. Security Measures">
            <ul className="list-disc list-inside space-y-1 text-muted-foreground">
              <li>JWT tokens verified server-side via Supabase Auth admin API</li>
              <li>Row Level Security — all database tables have RLS policies</li>
              <li>Encryption at rest — AES-256 via Supabase</li>
              <li>Encryption in transit — TLS 1.3 on all connections</li>
              <li>Rate limiting on all endpoints (per IP and per user)</li>
              <li>Security headers — HSTS, CSP, X-Frame-Options on all responses</li>
              <li>No logging of raw assessment answers — only scores are persisted</li>
            </ul>
          </Section>

          <Section title="8. Cookies and Tracking">
            <p className="text-muted-foreground">
              We use <strong className="text-foreground">session cookies only</strong> for Supabase Auth session management.
              No advertising cookies, no cross-site tracking, no third-party analytics in v1.
            </p>
          </Section>

          <Section title="9. Children&apos;s Privacy">
            <p className="text-muted-foreground">
              Volaura is not intended for users under 16. Contact{" "}
              <a href="mailto:privacy@volaura.az" className="text-primary underline">privacy@volaura.az</a>{" "}
              if you believe a minor has registered.
            </p>
          </Section>

          <Section title="10. Contact">
            <p className="text-muted-foreground">
              Questions? Email{" "}
              <a href="mailto:privacy@volaura.az" className="text-primary underline">privacy@volaura.az</a>.
              We respond to all privacy inquiries within 30 days.
            </p>
          </Section>

        </div>

        <div className="mt-16 pt-8 border-t border-white/10 text-center text-xs text-muted-foreground">
          <p>
            © 2026 Volaura ·{" "}
            <Link href={`/${locale}`} className="hover:text-foreground transition-colors">
              volaura.app
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="text-xl font-semibold mb-4">{title}</h2>
      <div className="space-y-3">{children}</div>
    </section>
  );
}

function PolicyTable({ headers, rows }: { headers: string[]; rows: string[][] }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-white/10">
      <table className="w-full text-xs">
        <thead>
          <tr className="bg-surface-container">
            {headers.map((h) => (
              <th key={h} className="text-left px-3 py-2 font-semibold border-b border-white/10">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className={i % 2 === 0 ? "" : "bg-surface-container/30"}>
              {row.map((cell, j) => (
                <td key={j} className="px-3 py-2 text-muted-foreground align-top">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
