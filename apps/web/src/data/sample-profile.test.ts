import { describe, it, expect } from "vitest";
import {
  SAMPLE_PROFILE,
  AURA_WEIGHTS,
  getSampleProfile,
  type CompetencyId,
} from "./sample-profile";

const ALL_COMPETENCIES: CompetencyId[] = [
  "communication",
  "reliability",
  "english_proficiency",
  "leadership",
  "event_performance",
  "tech_literacy",
  "adaptability",
  "empathy_safeguarding",
];

describe("AURA_WEIGHTS", () => {
  it("sums to 1.0", () => {
    const sum = Object.values(AURA_WEIGHTS).reduce((a, b) => a + b, 0);
    expect(sum).toBeCloseTo(1.0, 10);
  });

  it("has exactly 8 competencies", () => {
    expect(Object.keys(AURA_WEIGHTS)).toHaveLength(8);
  });

  it("contains all required competency IDs", () => {
    for (const id of ALL_COMPETENCIES) {
      expect(AURA_WEIGHTS).toHaveProperty(id);
    }
  });

  it("matches CLAUDE.md weights", () => {
    expect(AURA_WEIGHTS.communication).toBe(0.2);
    expect(AURA_WEIGHTS.reliability).toBe(0.15);
    expect(AURA_WEIGHTS.english_proficiency).toBe(0.15);
    expect(AURA_WEIGHTS.leadership).toBe(0.15);
    expect(AURA_WEIGHTS.event_performance).toBe(0.1);
    expect(AURA_WEIGHTS.tech_literacy).toBe(0.1);
    expect(AURA_WEIGHTS.adaptability).toBe(0.1);
    expect(AURA_WEIGHTS.empathy_safeguarding).toBe(0.05);
  });

  it("all weights are positive", () => {
    for (const w of Object.values(AURA_WEIGHTS)) {
      expect(w).toBeGreaterThan(0);
    }
  });
});

describe("SAMPLE_PROFILE", () => {
  it("totalAuraScore matches weighted computation", () => {
    let expected = 0;
    for (const id of ALL_COMPETENCIES) {
      expected += SAMPLE_PROFILE.competencyScores[id] * AURA_WEIGHTS[id];
    }
    expect(SAMPLE_PROFILE.totalAuraScore).toBe(Math.round(expected));
  });

  it("badgeTier matches totalAuraScore", () => {
    const score = SAMPLE_PROFILE.totalAuraScore;
    if (score >= 90) expect(SAMPLE_PROFILE.badgeTier).toBe("platinum");
    else if (score >= 75) expect(SAMPLE_PROFILE.badgeTier).toBe("gold");
    else if (score >= 60) expect(SAMPLE_PROFILE.badgeTier).toBe("silver");
    else if (score >= 40) expect(SAMPLE_PROFILE.badgeTier).toBe("bronze");
    else expect(SAMPLE_PROFILE.badgeTier).toBe("none");
  });

  it("totalHours equals sum of event hours", () => {
    const sum = SAMPLE_PROFILE.verifiedEvents.reduce((s, e) => s + e.hoursContributed, 0);
    expect(SAMPLE_PROFILE.totalHours).toBe(sum);
  });

  it("eventsCount equals verifiedEvents length", () => {
    expect(SAMPLE_PROFILE.eventsCount).toBe(SAMPLE_PROFILE.verifiedEvents.length);
  });

  it("has all 8 competency scores", () => {
    for (const id of ALL_COMPETENCIES) {
      expect(SAMPLE_PROFILE.competencyScores).toHaveProperty(id);
    }
  });

  it("all competency scores are 0-100", () => {
    for (const id of ALL_COMPETENCIES) {
      const score = SAMPLE_PROFILE.competencyScores[id];
      expect(score).toBeGreaterThanOrEqual(0);
      expect(score).toBeLessThanOrEqual(100);
    }
  });

  it("all events have verified=true", () => {
    for (const evt of SAMPLE_PROFILE.verifiedEvents) {
      expect(evt.verified).toBe(true);
    }
  });

  it("all events have valid attendanceRating 1-5", () => {
    for (const evt of SAMPLE_PROFILE.verifiedEvents) {
      expect(evt.attendanceRating).toBeGreaterThanOrEqual(1);
      expect(evt.attendanceRating).toBeLessThanOrEqual(5);
    }
  });

  it("all events have AZ titles and locations", () => {
    for (const evt of SAMPLE_PROFILE.verifiedEvents) {
      expect(evt.titleAz.length).toBeGreaterThan(0);
      expect(evt.locationAz.length).toBeGreaterThan(0);
    }
  });

  it("all events have positive hoursContributed", () => {
    for (const evt of SAMPLE_PROFILE.verifiedEvents) {
      expect(evt.hoursContributed).toBeGreaterThan(0);
    }
  });

  it("all events have valid ISO dates", () => {
    for (const evt of SAMPLE_PROFILE.verifiedEvents) {
      expect(new Date(evt.date).toISOString()).toBe(evt.date);
    }
  });
});

describe("getSampleProfile", () => {
  it("returns the same object as SAMPLE_PROFILE", () => {
    expect(getSampleProfile()).toBe(SAMPLE_PROFILE);
  });
});

describe("tier boundaries", () => {
  it("gold tier for score 83 (sample profile)", () => {
    expect(SAMPLE_PROFILE.totalAuraScore).toBe(83);
    expect(SAMPLE_PROFILE.badgeTier).toBe("gold");
  });
});
