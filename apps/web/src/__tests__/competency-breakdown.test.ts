import { describe, it, expect } from "vitest";

// ── getFreshnessInfo ──────────────────────────────────────────────────────────
// Extracted inline: ≤7 → cyan, ≤21 → amber, else muted

function getFreshnessInfo(daysSince: number) {
  if (daysSince <= 7) return { key: "freshnessRecent", color: "text-cyan-400" };
  if (daysSince <= 21) return { key: "freshnessWeeks", color: "text-amber-600" };
  return { key: "freshnessMonth", color: "text-muted-foreground" };
}

// ── RETEST_COOLDOWN_DAYS logic ────────────────────────────────────────────────
// From component: canRetake = daysSinceUpdate >= 7
//                 daysUntilRetake = max(0, 7 - daysSinceUpdate)

const RETEST_COOLDOWN_DAYS = 7;

function getRetakeState(daysSince: number | null) {
  const canRetake = daysSince !== null && daysSince >= RETEST_COOLDOWN_DAYS;
  const daysUntilRetake = daysSince !== null ? Math.max(0, RETEST_COOLDOWN_DAYS - daysSince) : null;
  return { canRetake, daysUntilRetake };
}

// ── daysSinceUpdate calculation ───────────────────────────────────────────────
// From component: Math.max(0, Math.floor((Date.now() - new Date(lastUpdated).getTime()) / 86_400_000))

function computeDaysSince(lastUpdated: string): number {
  return Math.max(0, Math.floor((Date.now() - new Date(lastUpdated).getTime()) / 86_400_000));
}

// ─────────────────────────────────────────────────────────────────────────────

describe("getFreshnessInfo — freshness key and color", () => {
  describe("≤7 days → recent (cyan)", () => {
    it("returns freshnessRecent + cyan for 0 days", () => {
      const result = getFreshnessInfo(0);
      expect(result.key).toBe("freshnessRecent");
      expect(result.color).toBe("text-cyan-400");
    });

    it("returns freshnessRecent + cyan for 1 day", () => {
      const result = getFreshnessInfo(1);
      expect(result.key).toBe("freshnessRecent");
      expect(result.color).toBe("text-cyan-400");
    });

    it("returns freshnessRecent + cyan for 7 days (boundary)", () => {
      const result = getFreshnessInfo(7);
      expect(result.key).toBe("freshnessRecent");
      expect(result.color).toBe("text-cyan-400");
    });

    it("returns correct structure shape for recent", () => {
      const result = getFreshnessInfo(3);
      expect(result).toHaveProperty("key");
      expect(result).toHaveProperty("color");
    });
  });

  describe("8–21 days → weeks (amber)", () => {
    it("returns freshnessWeeks + amber for 8 days (just past boundary)", () => {
      const result = getFreshnessInfo(8);
      expect(result.key).toBe("freshnessWeeks");
      expect(result.color).toBe("text-amber-600");
    });

    it("returns freshnessWeeks + amber for 14 days", () => {
      const result = getFreshnessInfo(14);
      expect(result.key).toBe("freshnessWeeks");
      expect(result.color).toBe("text-amber-600");
    });

    it("returns freshnessWeeks + amber for 21 days (boundary)", () => {
      const result = getFreshnessInfo(21);
      expect(result.key).toBe("freshnessWeeks");
      expect(result.color).toBe("text-amber-600");
    });
  });

  describe(">21 days → month (muted)", () => {
    it("returns freshnessMonth + muted for 22 days (just past boundary)", () => {
      const result = getFreshnessInfo(22);
      expect(result.key).toBe("freshnessMonth");
      expect(result.color).toBe("text-muted-foreground");
    });

    it("returns freshnessMonth + muted for 30 days", () => {
      const result = getFreshnessInfo(30);
      expect(result.key).toBe("freshnessMonth");
      expect(result.color).toBe("text-muted-foreground");
    });

    it("returns freshnessMonth + muted for 365 days", () => {
      const result = getFreshnessInfo(365);
      expect(result.key).toBe("freshnessMonth");
      expect(result.color).toBe("text-muted-foreground");
    });

    it("returns freshnessMonth + muted for very large value", () => {
      const result = getFreshnessInfo(9999);
      expect(result.key).toBe("freshnessMonth");
      expect(result.color).toBe("text-muted-foreground");
    });
  });
});

describe("getFreshnessInfo — boundary conditions", () => {
  it("7 is in the 'recent' bucket (≤7 inclusive)", () => {
    expect(getFreshnessInfo(7).key).toBe("freshnessRecent");
  });

  it("8 is in the 'weeks' bucket (first day past recent)", () => {
    expect(getFreshnessInfo(8).key).toBe("freshnessWeeks");
  });

  it("21 is in the 'weeks' bucket (≤21 inclusive)", () => {
    expect(getFreshnessInfo(21).key).toBe("freshnessWeeks");
  });

  it("22 is in the 'month' bucket (first day past weeks)", () => {
    expect(getFreshnessInfo(22).key).toBe("freshnessMonth");
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("canRetake — RETEST_COOLDOWN_DAYS = 7", () => {
  it("canRetake is false when daysSince is null (no prior assessment)", () => {
    const { canRetake } = getRetakeState(null);
    expect(canRetake).toBe(false);
  });

  it("canRetake is false when daysSince is 0", () => {
    const { canRetake } = getRetakeState(0);
    expect(canRetake).toBe(false);
  });

  it("canRetake is false when daysSince is 6", () => {
    const { canRetake } = getRetakeState(6);
    expect(canRetake).toBe(false);
  });

  it("canRetake is true when daysSince is exactly 7 (boundary)", () => {
    const { canRetake } = getRetakeState(7);
    expect(canRetake).toBe(true);
  });

  it("canRetake is true when daysSince is 8", () => {
    const { canRetake } = getRetakeState(8);
    expect(canRetake).toBe(true);
  });

  it("canRetake is true when daysSince is 30", () => {
    const { canRetake } = getRetakeState(30);
    expect(canRetake).toBe(true);
  });
});

describe("daysUntilRetake — countdown to cooldown expiry", () => {
  it("returns null when daysSince is null", () => {
    const { daysUntilRetake } = getRetakeState(null);
    expect(daysUntilRetake).toBeNull();
  });

  it("returns 7 when daysSince is 0 (full cooldown remaining)", () => {
    const { daysUntilRetake } = getRetakeState(0);
    expect(daysUntilRetake).toBe(7);
  });

  it("returns 1 when daysSince is 6 (one day left)", () => {
    const { daysUntilRetake } = getRetakeState(6);
    expect(daysUntilRetake).toBe(1);
  });

  it("returns 0 when daysSince is exactly 7 (cooldown complete)", () => {
    const { daysUntilRetake } = getRetakeState(7);
    expect(daysUntilRetake).toBe(0);
  });

  it("returns 0 (not negative) when daysSince is 8 (past cooldown)", () => {
    const { daysUntilRetake } = getRetakeState(8);
    expect(daysUntilRetake).toBe(0);
  });

  it("returns 0 when daysSince is 100", () => {
    const { daysUntilRetake } = getRetakeState(100);
    expect(daysUntilRetake).toBe(0);
  });
});

describe("canRetake + daysUntilRetake — combined state", () => {
  it("canRetake=false + daysUntilRetake=7 at day 0", () => {
    const state = getRetakeState(0);
    expect(state.canRetake).toBe(false);
    expect(state.daysUntilRetake).toBe(7);
  });

  it("canRetake=false + daysUntilRetake=3 at day 4", () => {
    const state = getRetakeState(4);
    expect(state.canRetake).toBe(false);
    expect(state.daysUntilRetake).toBe(3);
  });

  it("canRetake=true + daysUntilRetake=0 at day 7", () => {
    const state = getRetakeState(7);
    expect(state.canRetake).toBe(true);
    expect(state.daysUntilRetake).toBe(0);
  });

  it("canRetake=true + daysUntilRetake=0 at day 14", () => {
    const state = getRetakeState(14);
    expect(state.canRetake).toBe(true);
    expect(state.daysUntilRetake).toBe(0);
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("computeDaysSince — days since lastUpdated", () => {
  it("returns 0 for a date that is now", () => {
    const now = new Date().toISOString();
    const days = computeDaysSince(now);
    expect(days).toBe(0);
  });

  it("returns 0 for a date slightly in the future (guards against negative)", () => {
    const future = new Date(Date.now() + 60_000).toISOString(); // 1 min ahead
    const days = computeDaysSince(future);
    expect(days).toBe(0);
  });

  it("returns approximately 1 for a date 1 day ago", () => {
    const yesterday = new Date(Date.now() - 86_400_000).toISOString();
    const days = computeDaysSince(yesterday);
    expect(days).toBe(1);
  });

  it("returns approximately 7 for a date 7 days ago", () => {
    const sevenDaysAgo = new Date(Date.now() - 7 * 86_400_000).toISOString();
    const days = computeDaysSince(sevenDaysAgo);
    expect(days).toBe(7);
  });

  it("returns approximately 30 for a date 30 days ago", () => {
    const thirtyDaysAgo = new Date(Date.now() - 30 * 86_400_000).toISOString();
    const days = computeDaysSince(thirtyDaysAgo);
    expect(days).toBe(30);
  });

  it("floors partial days (23 hours = 0 days)", () => {
    const almostOneDay = new Date(Date.now() - 23 * 3600_000).toISOString();
    const days = computeDaysSince(almostOneDay);
    expect(days).toBe(0);
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("freshness + retake — integration: freshness category aligns with retake state", () => {
  it("fresh assessment (day 0): recent freshness + cannot retake", () => {
    const freshness = getFreshnessInfo(0);
    const { canRetake } = getRetakeState(0);
    expect(freshness.key).toBe("freshnessRecent");
    expect(canRetake).toBe(false);
  });

  it("day 7: still recent freshness + just became retakeable", () => {
    const freshness = getFreshnessInfo(7);
    const { canRetake, daysUntilRetake } = getRetakeState(7);
    expect(freshness.key).toBe("freshnessRecent");
    expect(canRetake).toBe(true);
    expect(daysUntilRetake).toBe(0);
  });

  it("day 14: weeks freshness + can retake", () => {
    const freshness = getFreshnessInfo(14);
    const { canRetake } = getRetakeState(14);
    expect(freshness.key).toBe("freshnessWeeks");
    expect(canRetake).toBe(true);
  });

  it("day 30: month freshness + can retake", () => {
    const freshness = getFreshnessInfo(30);
    const { canRetake } = getRetakeState(30);
    expect(freshness.key).toBe("freshnessMonth");
    expect(canRetake).toBe(true);
  });
});
