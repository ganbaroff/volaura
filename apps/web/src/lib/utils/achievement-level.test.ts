import { describe, it, expect } from "vitest";
import { getAchievementLevelKey } from "./achievement-level";

describe("getAchievementLevelKey", () => {
  it("returns Expert for percentile >= 95", () => {
    expect(getAchievementLevelKey(95)).toBe("profile.achievementExpert");
    expect(getAchievementLevelKey(100)).toBe("profile.achievementExpert");
    expect(getAchievementLevelKey(99.9)).toBe("profile.achievementExpert");
  });

  it("returns Advanced for percentile 85-94", () => {
    expect(getAchievementLevelKey(85)).toBe("profile.achievementAdvanced");
    expect(getAchievementLevelKey(94)).toBe("profile.achievementAdvanced");
    expect(getAchievementLevelKey(94.9)).toBe("profile.achievementAdvanced");
  });

  it("returns Proficient for percentile 70-84", () => {
    expect(getAchievementLevelKey(70)).toBe("profile.achievementProficient");
    expect(getAchievementLevelKey(84)).toBe("profile.achievementProficient");
    expect(getAchievementLevelKey(84.9)).toBe("profile.achievementProficient");
  });

  it("returns Growing for percentile 50-69", () => {
    expect(getAchievementLevelKey(50)).toBe("profile.achievementGrowing");
    expect(getAchievementLevelKey(69)).toBe("profile.achievementGrowing");
  });

  it("returns Building for percentile 25-49", () => {
    expect(getAchievementLevelKey(25)).toBe("profile.achievementBuilding");
    expect(getAchievementLevelKey(49)).toBe("profile.achievementBuilding");
  });

  it("returns Starting for percentile < 25", () => {
    expect(getAchievementLevelKey(0)).toBe("profile.achievementStarting");
    expect(getAchievementLevelKey(24)).toBe("profile.achievementStarting");
    expect(getAchievementLevelKey(24.9)).toBe("profile.achievementStarting");
  });

  it("handles exact boundary values", () => {
    expect(getAchievementLevelKey(25)).toBe("profile.achievementBuilding");
    expect(getAchievementLevelKey(50)).toBe("profile.achievementGrowing");
    expect(getAchievementLevelKey(70)).toBe("profile.achievementProficient");
    expect(getAchievementLevelKey(85)).toBe("profile.achievementAdvanced");
    expect(getAchievementLevelKey(95)).toBe("profile.achievementExpert");
  });

  it("handles negative values as Starting", () => {
    expect(getAchievementLevelKey(-1)).toBe("profile.achievementStarting");
    expect(getAchievementLevelKey(-100)).toBe("profile.achievementStarting");
  });
});
