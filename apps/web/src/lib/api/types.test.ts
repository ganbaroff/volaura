import { describe, it, expect } from "vitest";
import { toAuraScore, toProfile } from "./types";
import type { AuraScoreResponse, ProfileResponse } from "./generated/types.gen";

describe("toAuraScore", () => {
  const base: AuraScoreResponse = {
    professional_id: "uuid-1",
    total_score: 82,
    effective_score: 78,
    badge_tier: "gold",
    elite_status: true,
    competency_scores: { communication: 85, reliability: 90 },
    reliability_score: 0.95,
    reliability_status: "high",
    events_attended: 12,
    events_no_show: 1,
    percentile_rank: 88,
    aura_history: [{ date: "2026-01-01", score: 75 }],
    last_updated: "2026-04-18T09:00:00Z",
  };

  it("maps elite_status to is_elite", () => {
    const result = toAuraScore(base);
    expect(result.is_elite).toBe(true);
    expect(result).not.toHaveProperty("elite_status");
  });

  it("preserves all numeric fields", () => {
    const result = toAuraScore(base);
    expect(result.total_score).toBe(82);
    expect(result.effective_score).toBe(78);
    expect(result.reliability_score).toBe(0.95);
    expect(result.events_attended).toBe(12);
    expect(result.events_no_show).toBe(1);
    expect(result.percentile_rank).toBe(88);
  });

  it("preserves competency_scores object", () => {
    const result = toAuraScore(base);
    expect(result.competency_scores).toEqual({ communication: 85, reliability: 90 });
  });

  it("handles null effective_score", () => {
    const result = toAuraScore({ ...base, effective_score: null });
    expect(result.effective_score).toBeNull();
  });

  it("handles null percentile_rank", () => {
    const result = toAuraScore({ ...base, percentile_rank: null });
    expect(result.percentile_rank).toBeNull();
  });

  it("defaults badge_tier to 'none' when falsy", () => {
    const result = toAuraScore({ ...base, badge_tier: "" });
    expect(result.badge_tier).toBe("none");
  });

  it("passes through valid badge_tier", () => {
    for (const tier of ["platinum", "gold", "silver", "bronze"] as const) {
      const result = toAuraScore({ ...base, badge_tier: tier });
      expect(result.badge_tier).toBe(tier);
    }
  });

  it("preserves aura_history array", () => {
    const result = toAuraScore(base);
    expect(result.aura_history).toEqual([{ date: "2026-01-01", score: 75 }]);
  });

  it("preserves last_updated", () => {
    const result = toAuraScore(base);
    expect(result.last_updated).toBe("2026-04-18T09:00:00Z");
  });
});

describe("toProfile", () => {
  const base: ProfileResponse = {
    id: "uuid-2",
    username: "testuser",
    display_name: "Test User",
    avatar_url: "https://example.com/avatar.jpg",
    bio: "Hello",
    location: "Baku",
    languages: ["az", "en"],
    is_public: true,
    visible_to_orgs: true,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-04-18T00:00:00Z",
    registration_number: 42,
    registration_tier: "gold",
  };

  it("maps all fields directly", () => {
    const result = toProfile(base);
    expect(result.id).toBe("uuid-2");
    expect(result.username).toBe("testuser");
    expect(result.display_name).toBe("Test User");
    expect(result.avatar_url).toBe("https://example.com/avatar.jpg");
    expect(result.bio).toBe("Hello");
    expect(result.location).toBe("Baku");
    expect(result.languages).toEqual(["az", "en"]);
    expect(result.is_public).toBe(true);
    expect(result.visible_to_orgs).toBe(true);
    expect(result.registration_number).toBe(42);
    expect(result.registration_tier).toBe("gold");
  });

  it("defaults display_name to null when undefined", () => {
    const result = toProfile({ ...base, display_name: undefined } as unknown as ProfileResponse);
    expect(result.display_name).toBeNull();
  });

  it("defaults avatar_url to null when undefined", () => {
    const result = toProfile({ ...base, avatar_url: undefined } as unknown as ProfileResponse);
    expect(result.avatar_url).toBeNull();
  });

  it("defaults bio to null when undefined", () => {
    const result = toProfile({ ...base, bio: undefined } as unknown as ProfileResponse);
    expect(result.bio).toBeNull();
  });

  it("defaults location to null when undefined", () => {
    const result = toProfile({ ...base, location: undefined } as unknown as ProfileResponse);
    expect(result.location).toBeNull();
  });

  it("defaults languages to empty array when undefined", () => {
    const result = toProfile({ ...base, languages: undefined } as unknown as ProfileResponse);
    expect(result.languages).toEqual([]);
  });

  it("defaults is_public to false when undefined", () => {
    const result = toProfile({ ...base, is_public: undefined } as unknown as ProfileResponse);
    expect(result.is_public).toBe(false);
  });

  it("defaults visible_to_orgs to false when undefined", () => {
    const result = toProfile({ ...base, visible_to_orgs: undefined } as unknown as ProfileResponse);
    expect(result.visible_to_orgs).toBe(false);
  });

  it("defaults registration_number to null when undefined", () => {
    const result = toProfile({ ...base, registration_number: undefined } as unknown as ProfileResponse);
    expect(result.registration_number).toBeNull();
  });

  it("defaults registration_tier to null when undefined", () => {
    const result = toProfile({ ...base, registration_tier: undefined } as unknown as ProfileResponse);
    expect(result.registration_tier).toBeNull();
  });

  it("preserves timestamps", () => {
    const result = toProfile(base);
    expect(result.created_at).toBe("2026-01-01T00:00:00Z");
    expect(result.updated_at).toBe("2026-04-18T00:00:00Z");
  });
});
