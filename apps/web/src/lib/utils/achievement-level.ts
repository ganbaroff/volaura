/**
 * CIS-001 fix — Achievement Level mapping for percentile_rank.
 *
 * Problem: "Top 5%" framing is competitive and alienates users in collectivist
 * cultures (Azerbaijan, Central Asia). Users feel ranked against each other
 * rather than measured against their own growth.
 *
 * Fix: Map percentile_rank to achievement level labels.
 * Display "Expert" instead of "Top 5%" — same data, non-competitive framing.
 *
 * topPercent is kept for social share text (explicit competition context where
 * users have opted into sharing — acceptable there).
 */

/** Map percentile_rank (0–100) to a profile.achievement* i18n key. */
export function getAchievementLevelKey(percentileRank: number): string {
  // percentileRank: higher = better (% of users you outperform)
  if (percentileRank >= 95) return "profile.achievementExpert";
  if (percentileRank >= 85) return "profile.achievementAdvanced";
  if (percentileRank >= 70) return "profile.achievementProficient";
  if (percentileRank >= 50) return "profile.achievementGrowing";
  if (percentileRank >= 25) return "profile.achievementBuilding";
  return "profile.achievementStarting";
}
