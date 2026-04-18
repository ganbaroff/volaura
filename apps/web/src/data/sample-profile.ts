/**
 * Sample Profile Fixture — public /sample route
 *
 * Purpose: deterministic data for the landing demo "See a real profile" link.
 *   - No PII, no real person
 *   - Identity: "Sample Professional"
 *   - AURA total: 83 (Gold tier, ≥75)
 *   - 8 competencies wired to AURA weights from CLAUDE.md
 *   - 3 verified events with organizer + attendance rating + date
 *
 * Drafted 2026-04-17 by Cowork-Atlas so Terminal-Atlas can focus on the UI,
 * not re-inventing the data shape. Matches the `competencyScores` prop of
 * AuraRadarChart component prop types.
 *
 * If the real API response shape changes, update BOTH this fixture and the
 * `/sample` page consumer — fixture must stay a valid stand-in so we can
 * screenshot it for WUF13 without touching production data.
 */

export type CompetencyId =
  | "communication"
  | "reliability"
  | "english_proficiency"
  | "leadership"
  | "event_performance"
  | "tech_literacy"
  | "adaptability"
  | "empathy_safeguarding";

export type BadgeTier = "platinum" | "gold" | "silver" | "bronze" | "none";

export interface SampleVerifiedEvent {
  id: string;
  title: string;
  titleAz: string;
  organizerName: string;
  location: string;
  locationAz: string;
  date: string; // ISO
  hoursContributed: number;
  attendanceRating: 1 | 2 | 3 | 4 | 5;
  role: string;
  verified: true;
}

export interface SampleProfile {
  id: string;
  displayName: string;
  tagline: string;
  taglineAz: string;
  joinedAt: string; // ISO
  totalAuraScore: number; // 0-100, weighted
  badgeTier: BadgeTier;
  competencyScores: Record<CompetencyId, number>;
  verifiedEvents: SampleVerifiedEvent[];
  totalHours: number;
  eventsCount: number;
}

// AURA weights — must mirror CLAUDE.md. Any change here = change the backend
// first (app/core/assessment/engine.py), never diverge silently.
export const AURA_WEIGHTS: Record<CompetencyId, number> = {
  communication: 0.2,
  reliability: 0.15,
  english_proficiency: 0.15,
  leadership: 0.15,
  event_performance: 0.1,
  tech_literacy: 0.1,
  adaptability: 0.1,
  empathy_safeguarding: 0.05,
};

function computeTotal(scores: Record<CompetencyId, number>): number {
  let total = 0;
  for (const id of Object.keys(AURA_WEIGHTS) as CompetencyId[]) {
    total += scores[id] * AURA_WEIGHTS[id];
  }
  return Math.round(total);
}

function tierFor(score: number): BadgeTier {
  if (score >= 90) return "platinum";
  if (score >= 75) return "gold";
  if (score >= 60) return "silver";
  if (score >= 40) return "bronze";
  return "none";
}

const competencyScores: Record<CompetencyId, number> = {
  communication: 85,
  reliability: 88,
  english_proficiency: 80,
  leadership: 78,
  event_performance: 82,
  tech_literacy: 84,
  adaptability: 79,
  empathy_safeguarding: 86,
};

const verifiedEvents: SampleVerifiedEvent[] = [
  {
    id: "sample-evt-001",
    title: "Environmental Awareness Campaign",
    titleAz: "Ətraf Mühit Maarifçilik Kampaniyası",
    organizerName: "Green Azerbaijan NGO",
    location: "Baku, Heydar Aliyev Center",
    locationAz: "Bakı, Heydər Əliyev Mərkəzi",
    date: "2026-03-22T09:00:00.000Z",
    hoursContributed: 6,
    attendanceRating: 5,
    role: "Community Outreach Lead",
    verified: true,
  },
  {
    id: "sample-evt-002",
    title: "Youth Tech Workshop",
    titleAz: "Gənclər Texnologiya Seminarı",
    organizerName: "TechHub Baku",
    location: "Sumgait, Youth Center",
    locationAz: "Sumqayıt, Gənclər Mərkəzi",
    date: "2026-02-15T10:00:00.000Z",
    hoursContributed: 4,
    attendanceRating: 5,
    role: "Coding Mentor",
    verified: true,
  },
  {
    id: "sample-evt-003",
    title: "Cultural Heritage Documentation",
    titleAz: "Mədəni İrs Sənədləşdirilməsi",
    organizerName: "Azerbaijan Heritage Society",
    location: "Sheki, Old City",
    locationAz: "Şəki, Köhnə Şəhər",
    date: "2026-01-18T08:00:00.000Z",
    hoursContributed: 12,
    attendanceRating: 4,
    role: "Field Photographer",
    verified: true,
  },
];

const totalScore = computeTotal(competencyScores);

export const SAMPLE_PROFILE: SampleProfile = {
  id: "sample-professional",
  displayName: "Sample Professional",
  tagline: "A fictional profile — shows what a verified AURA looks like.",
  taglineAz: "Nümunəvi profil — təsdiqlənmiş AURA necə görünür.",
  joinedAt: "2025-11-01T12:00:00.000Z",
  totalAuraScore: totalScore,
  badgeTier: tierFor(totalScore),
  competencyScores,
  verifiedEvents,
  totalHours: verifiedEvents.reduce((sum, e) => sum + e.hoursContributed, 0),
  eventsCount: verifiedEvents.length,
};

export function getSampleProfile(): SampleProfile {
  return SAMPLE_PROFILE;
}
