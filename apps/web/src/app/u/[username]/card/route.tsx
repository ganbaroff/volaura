/**
 * AURA Card image endpoint — `/u/[username]/card`
 *
 * Returns a dynamic OG image (1200×630) using Next.js ImageResponse (Satori).
 * Format can be overridden via ?format=story (1080×1920) or ?format=square (1080×1080).
 */

import { ImageResponse } from "next/og";
import type { NextRequest } from "next/server";

export const runtime = "edge";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface PublicProfile {
  id: string;
  username: string;
  display_name: string | null;
  badge_issued_at: string | null;
}

interface AuraScore {
  overall_score: number;
  badge_tier: string;
  elite_status: boolean;
  competency_scores: Record<string, number>;
}

const BADGE_COLORS: Record<string, string> = {
  platinum: "#a78bfa",
  gold: "#facc15",
  silver: "#94a3b8",
  bronze: "#d97706",
  none: "#6366f1",
};

const COMPETENCY_LABELS: Record<string, string> = {
  communication: "Comm",
  reliability: "Relbl",
  english_proficiency: "Eng",
  leadership: "Lead",
  event_performance: "Event",
  tech_literacy: "Tech",
  adaptability: "Adapt",
  empathy_safeguarding: "Empth",
};

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ username: string }> }
) {
  const { username } = await params;

  const format = request.nextUrl.searchParams.get("format") ?? "linkedin";
  const [width, height] =
    format === "story" ? [1080, 1920] : format === "square" ? [1080, 1080] : [1200, 630];

  // Fetch data
  let profile: PublicProfile | null = null;
  let aura: AuraScore | null = null;

  try {
    const [pRes, aRes] = await Promise.all([
      fetch(`${API_URL}/api/profiles/${username}`),
      fetch(`${API_URL}/api/aura/${username}`).then(() => null).catch(() => null), // placeholder; will fix after profile fetch
    ]);

    if (pRes.ok) {
      profile = await pRes.json();
      // Now fetch aura by volunteer_id
      if (profile) {
        const aRes2 = await fetch(`${API_URL}/api/aura/${profile.id}`);
        if (aRes2.ok) aura = await aRes2.json();
      }
    }
  } catch {
    // fallback to placeholder
  }

  const name = profile?.display_name ?? profile?.username ?? username;
  const score = aura?.overall_score?.toFixed(1) ?? "—";
  const tier = aura?.badge_tier ?? "none";
  const badgeColor = BADGE_COLORS[tier] ?? BADGE_COLORS.none;
  const isElite = aura?.elite_status ?? false;
  const competencyScores = aura?.competency_scores ?? {};

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          background: "linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 60%, #16213e 100%)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "system-ui, sans-serif",
          padding: 60,
          color: "#f1f5f9",
        }}
      >
        {/* Brand */}
        <div style={{ position: "absolute", top: 36, left: 48, fontSize: 22, fontWeight: 700, color: "#818cf8", display: "flex" }}>
          VOLAURA
        </div>

        {/* Score */}
        <div style={{ fontSize: 100, fontWeight: 900, color: badgeColor, lineHeight: 1, display: "flex" }}>
          {score}
        </div>

        {/* Badge label */}
        <div style={{ fontSize: 24, fontWeight: 600, color: badgeColor, marginTop: 8, textTransform: "uppercase", letterSpacing: 4, display: "flex" }}>
          {tier}{isElite ? " · ELITE" : ""}
        </div>

        {/* Name */}
        <div style={{ fontSize: 32, fontWeight: 700, color: "#f1f5f9", marginTop: 20, display: "flex" }}>
          {name}
        </div>
        <div style={{ fontSize: 18, color: "#94a3b8", marginTop: 4, display: "flex" }}>
          @{username}
        </div>

        {/* Competency bars */}
        {Object.keys(COMPETENCY_LABELS).length > 0 && (
          <div
            style={{
              display: "flex",
              flexDirection: "row",
              gap: 10,
              marginTop: 40,
              alignItems: "flex-end",
            }}
          >
            {Object.entries(COMPETENCY_LABELS).map(([slug, label]) => {
              const val = competencyScores[slug] ?? 0;
              const barH = Math.max(4, Math.round((val / 100) * 80));
              return (
                <div key={slug} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
                  <div
                    style={{
                      width: 28,
                      height: barH,
                      background: badgeColor,
                      borderRadius: 4,
                      opacity: val > 0 ? 1 : 0.2,
                    }}
                  />
                  <div style={{ fontSize: 10, color: "#64748b", display: "flex" }}>{label}</div>
                </div>
              );
            })}
          </div>
        )}

        {/* Footer */}
        <div style={{ position: "absolute", bottom: 36, right: 48, fontSize: 14, color: "#475569", display: "flex" }}>
          volaura.app
        </div>
      </div>
    ),
    { width, height }
  );
}
