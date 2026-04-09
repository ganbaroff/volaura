import { ImageResponse } from "next/og";
import type { NextRequest } from "next/server";

export const runtime = "edge";

const BADGE_COLORS: Record<string, string> = {
  platinum: "#e5e4e2",
  gold: "#ffd700",
  silver: "#c0c0c0",
  bronze: "#cd7f32",
  none: "#908fa0",
};

const IDENTITY_LABELS: Record<string, string> = {
  platinum: "Platinum-level Professional",
  gold: "Gold-level Professional",
  silver: "Silver-level Professional",
  bronze: "Bronze-level Professional",
  none: "Volaura Professional",
};

const ALLOWED_TIERS = new Set(["platinum", "gold", "silver", "bronze", "none"]);

const COMP_LABELS: Record<string, string> = {
  comm: "Communication",
  lead: "Leadership",
  eng: "English Proficiency",
  tech: "Tech Literacy",
  rel: "Reliability",
  adapt: "Adaptability",
  event: "Event Performance",
  emp: "Empathy & Safety",
};

const BAR_COLORS = ["#34d399", "#c0c1ff", "#bdc2ff", "#e9c400", "#34d399", "#c0c1ff", "#bdc2ff", "#d4b4ff"];

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);

  // --- Input validation & sanitization ---
  const name = (searchParams.get("name") || "Professional").slice(0, 60);
  // score: only digits and one decimal point, max 6 chars
  const rawScore = searchParams.get("score") || "0";
  const score = /^\d{1,3}(\.\d{1,2})?$/.test(rawScore) ? rawScore : "0";
  // tier: must be in the allowed set
  const rawTier = searchParams.get("tier") || "none";
  const tier = ALLOWED_TIERS.has(rawTier) ? rawTier : "none";
  const username = (searchParams.get("username") || "").replace(/[^\w.-]/g, "").slice(0, 50);
  const regNum = (searchParams.get("reg") || "").replace(/[^\d]/g, "").slice(0, 10);

  const tierColor = BADGE_COLORS[tier];
  const identity = IDENTITY_LABELS[tier];

  // comps: limit to 8 entries, validate slug (alphanumeric) and score (numeric)
  const compsRaw = searchParams.get("comps") || "";
  const comps = compsRaw
    .split(",")
    .filter(Boolean)
    .slice(0, 8)
    .map((c) => {
      const [slug = "", val = "0"] = c.split(":");
      const safeSlug = slug.replace(/[^\w]/g, "").slice(0, 20);
      const safeScore = Math.min(100, Math.max(0, Number(val) || 0));
      return { slug: safeSlug, score: safeScore };
    })
    .filter((c) => c.slug);

  const response = new ImageResponse(
    (
      <div
        style={{
          width: 1200,
          height: 630,
          display: "flex",
          background: "#0d0d15",
          fontFamily: "Inter, sans-serif",
          color: "#e4e1ed",
          position: "relative",
        }}
      >
        {/* Ambient glow */}
        <div
          style={{
            position: "absolute",
            top: -100,
            left: -50,
            width: 500,
            height: 500,
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(192,193,255,0.08) 0%, transparent 70%)",
          }}
        />

        {/* Left: Identity */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            padding: "60px",
            width: "50%",
          }}
        >
          <div style={{ fontSize: 14, fontWeight: 700, color: "#c0c1ff", letterSpacing: 2, marginBottom: 16 }}>
            VOLAURA
          </div>
          <div style={{ fontSize: 36, fontWeight: 700, color: "#e4e1ed", marginBottom: 8 }}>
            {name}
          </div>
          <div style={{ fontSize: 22, fontWeight: 700, color: tierColor, marginBottom: 12 }}>
            {identity}
          </div>
          <div style={{ fontSize: 16, color: "#908fa0", marginBottom: 24 }}>
            AURA Score: {score} / 100
          </div>

          <div style={{ display: "flex", gap: 8 }}>
            <div
              style={{
                padding: "6px 16px",
                borderRadius: 16,
                background: `${tierColor}22`,
                color: tierColor,
                fontSize: 12,
                fontWeight: 700,
                letterSpacing: 1,
              }}
            >
              {tier.toUpperCase()}
            </div>
            <div
              style={{
                padding: "6px 16px",
                borderRadius: 16,
                background: "#34d39918",
                color: "#34d399",
                fontSize: 12,
                fontWeight: 600,
              }}
            >
              Verified
            </div>
          </div>

          {username && (
            <div style={{ fontSize: 13, color: "#908fa0", marginTop: 20 }}>
              volaura.app/u/{username}
              {regNum && ` · #${regNum}`}
            </div>
          )}
        </div>

        {/* Right: Competency bars */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            padding: "60px 60px 60px 0",
            width: "50%",
          }}
        >
          <div style={{ fontSize: 16, fontWeight: 600, color: "#c7c4d7", marginBottom: 20 }}>
            Skill Profile
          </div>
          {comps.map((comp, i) => (
            <div key={comp.slug} style={{ display: "flex", flexDirection: "column", marginBottom: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ fontSize: 13, fontWeight: 500, color: "#e4e1ed" }}>
                  {COMP_LABELS[comp.slug] || comp.slug}
                </span>
                <span style={{ fontSize: 13, fontWeight: 700, color: BAR_COLORS[i % BAR_COLORS.length] }}>
                  {comp.score}
                </span>
              </div>
              <div
                style={{
                  width: "100%",
                  height: 6,
                  borderRadius: 3,
                  background: "#1b1b23",
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    width: `${comp.score}%`,
                    height: "100%",
                    borderRadius: 3,
                    background: BAR_COLORS[i % BAR_COLORS.length],
                  }}
                />
              </div>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div
          style={{
            position: "absolute",
            bottom: 0,
            left: 0,
            right: 0,
            height: 36,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "0 60px",
            background: "rgba(13,13,21,0.9)",
            fontSize: 11,
            color: "#908fa0",
          }}
        >
          <span>Verified by Volaura · volaura.app</span>
          <span>Adaptive assessment powered by IRT/CAT</span>
        </div>
      </div>
    ),
    {
      width: 1200,
      height: 630,
    },
  );

  // Cache at CDN for 1 hour; allow stale serving for 24h
  response.headers.set("Cache-Control", "public, s-maxage=3600, stale-while-revalidate=86400");
  return response;
}
