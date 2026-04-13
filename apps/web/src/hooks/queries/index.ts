// Hook barrel — generated SDK handles auth via client interceptor (ADR-003)
// Hooks not yet migrated to SDK: leaderboard, brandedby, public-stats, aura-explanation (endpoints not in OpenAPI spec)
export { useAuraScore, useAuraScoreByProfessional } from "./use-aura";
export { useAuraExplanation } from "./use-aura-explanation";
export type { AuraExplanationResponse, CompetencyExplanation, EvaluationItem, ConceptScore } from "./use-aura-explanation";
export { useProfile, usePublicProfile, useUpdateProfile } from "./use-profile";
export { useBadges, useActivity, useDashboardStats } from "./use-dashboard";
export { useAuthToken } from "./use-auth-token";
export { useEvents, useEvent, useMyEvents, useCreateEvent, useRegisterForEvent } from "./use-events";
export { useMyOrganization, useOrganizations, useCreateOrganization, useUpdateOrganization } from "./use-organizations";
export { useLeaderboard } from "./use-leaderboard";
export type { LeaderboardEntry, LeaderboardResponse, LeaderboardPeriod } from "./use-leaderboard";
export { usePublicStats } from "./use-public-stats";
export type { PublicStats } from "./use-public-stats";
export { useSkill } from "./use-skill";
export type { SkillResponse } from "./use-skill";
export { useSubscription } from "./use-subscription";
export type { SubscriptionStatus, UseSubscriptionResult } from "./use-subscription";
