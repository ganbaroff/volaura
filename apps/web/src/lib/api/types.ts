/**
 * INTERIM API types — manually written to match FastAPI Pydantic schemas.
 * TODO: Replace with @hey-api/openapi-ts generated types after `pnpm generate:api`
 */

// ── AURA ─────────────────────────────────────────────────────────────────────

export interface AuraScore {
  volunteer_id: string;
  total_score: number;
  badge_tier: "platinum" | "gold" | "silver" | "bronze" | "none";
  is_elite: boolean;
  competency_scores: Record<string, number>;
  verification_level: string;
  last_updated: string;
}

// ── Profile ──────────────────────────────────────────────────────────────────

export interface Profile {
  id: string;
  username: string;
  display_name: string | null;
  avatar_url: string | null;
  bio: string | null;
  location: string | null;
  languages: string[];
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface UpdateProfileRequest {
  display_name?: string;
  bio?: string;
  location?: string;
  languages?: string[];
  is_public?: boolean;
}

// ── Assessment ───────────────────────────────────────────────────────────────

export interface QuestionOut {
  id: string;
  question_type: string;
  question_en: string;
  question_az: string;
  options: string[] | null;
  competency_id: string;
}

export interface SessionOut {
  session_id: string;
  competency_slug: string;
  questions_answered: number;
  theta: number;
  theta_se: number;
  is_complete: boolean;
  stop_reason: string | null;
  next_question: QuestionOut | null;
}

export interface AssessmentResultOut {
  session_id: string;
  competency_slug: string;
  theta: number;
  theta_se: number;
  competency_score: number;
  questions_answered: number;
  stop_reason: string | null;
  aura_updated: boolean;
  gaming_flags: string[];
  completed_at: string | null;
}

// ── Auth ─────────────────────────────────────────────────────────────────────

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  expires_in: number;
}

export interface AuthMeResponse {
  user_id: string;
  email: string;
  profile: Profile | null;
}

// ── Badges ───────────────────────────────────────────────────────────────────

export interface Badge {
  id: string;
  volunteer_id: string;
  badge_type: string;
  tier: string;
  earned_at: string;
  metadata: Record<string, unknown>;
}

// ── Events ───────────────────────────────────────────────────────────────────

/** @deprecated Use EventResponse — this was the mock-data shape */
export interface Event {
  id: string;
  title: string;
  description: string;
  start_date: string;
  end_date: string | null;
  location: string | null;
  status: "upcoming" | "active" | "completed" | "cancelled";
  max_volunteers: number | null;
  registered_count: number;
  tags: string[];
  created_at: string;
}

// TODO: Replace with @hey-api/openapi-ts generated types after `pnpm generate:api`

export interface EventResponse {
  id: string;
  organization_id: string;
  title_en: string;
  title_az: string;
  description_en: string | null;
  description_az: string | null;
  event_type: string | null;
  location: string | null;
  location_coords: Record<string, number> | null;
  start_date: string;
  end_date: string;
  capacity: number | null;
  required_min_aura: number;
  required_languages: string[];
  status: "draft" | "open" | "closed" | "cancelled" | "completed";
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface EventCreate {
  title_en: string;
  title_az: string;
  description_en?: string;
  description_az?: string;
  event_type?: string;
  location?: string;
  start_date: string;
  end_date: string;
  capacity?: number;
  required_min_aura?: number;
  required_languages?: string[];
  status?: "draft" | "open";
  is_public?: boolean;
}

export interface RegistrationResponse {
  id: string;
  event_id: string;
  volunteer_id: string;
  status: string;
  registered_at: string;
  checked_in_at: string | null;
  check_in_code: string | null;
  coordinator_rating: number | null;
  coordinator_feedback: string | null;
  volunteer_rating: number | null;
  volunteer_feedback: string | null;
}

// ── Organizations ─────────────────────────────────────────────────────────────

// TODO: Replace with @hey-api/openapi-ts generated types after `pnpm generate:api`

export interface OrganizationResponse {
  id: string;
  owner_id: string;
  name: string;
  description: string | null;
  website_url: string | null;
  logo_url: string | null;
  contact_email: string | null;
  is_verified: boolean;
  subscription_tier: string;
  trust_score: number | null;
  created_at: string;
  updated_at: string;
}

export interface OrganizationCreate {
  name: string;
  description?: string;
  website_url?: string;
  logo_url?: string;
  contact_email?: string;
}

// ── Activity ─────────────────────────────────────────────────────────────────

export interface ActivityItem {
  id: string;
  type: "assessment" | "event" | "verification" | "badge";
  description: string;
  created_at: string;
  metadata: Record<string, unknown>;
}

// ── Dashboard ────────────────────────────────────────────────────────────────

export interface DashboardStats {
  events_attended: number;
  total_hours: number;
  verified_skills: number;
  streak_days: number;
}
