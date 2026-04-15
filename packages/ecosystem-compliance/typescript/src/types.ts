/**
 * Ecosystem-wide GDPR Art.22 + EU AI Act compliance types.
 *
 * Zod v3 schemas + inferred TypeScript types. Mirrors the 4 Postgres
 * tables in supabase/migrations/20260415230000_ecosystem_compliance_schema.sql.
 *
 * Each product (volaura, mindshift, lifesim, brandedby, zeus) imports
 * these and inserts via its own Supabase service_role client.
 */
import { z } from "zod";

// ---------------------------------------------------------------------------
// Shared enums — mirror DB CHECK constraints exactly.
// ---------------------------------------------------------------------------
export const SourceProduct = z.enum([
  "volaura",
  "mindshift",
  "lifesim",
  "brandedby",
  "zeus",
]);
export type SourceProduct = z.infer<typeof SourceProduct>;

export const DocumentType = z.enum([
  "privacy_policy",
  "terms_of_service",
  "ai_decision_notice",
  "cookie_policy",
  "data_processing_agreement",
]);
export type DocumentType = z.infer<typeof DocumentType>;

export const Locale = z.enum(["az", "en", "ru"]);
export type Locale = z.infer<typeof Locale>;

export const ConsentEventType = z.enum([
  "consent_given",
  "consent_withdrawn",
  "consent_updated",
  "policy_reaccepted",
]);
export type ConsentEventType = z.infer<typeof ConsentEventType>;

export const HumanReviewStatus = z.enum([
  "pending",
  "in_review",
  "resolved_uphold",
  "resolved_overturn",
  "escalated_to_authority",
]);
export type HumanReviewStatus = z.infer<typeof HumanReviewStatus>;

// ISO 8601 timestamp; Supabase returns strings, callers can Date-ify as needed.
const ISODateTime = z.string().datetime({ offset: true });
const UUID = z.string().uuid();

// ---------------------------------------------------------------------------
// 1. policy_versions
// ---------------------------------------------------------------------------
export const PolicyVersionCreateSchema = z.object({
  document_type: DocumentType,
  version: z.string().min(1),
  locale: Locale,
  content_markdown: z.string().min(1),
  effective_from: ISODateTime,
  superseded_by: UUID.nullable().optional(),
  // content_sha256 filled by DB trigger.
});
export type PolicyVersionCreate = z.infer<typeof PolicyVersionCreateSchema>;

export const PolicyVersionSchema = PolicyVersionCreateSchema.extend({
  id: UUID,
  content_sha256: z.string(),
  created_at: ISODateTime,
});
export type PolicyVersion = z.infer<typeof PolicyVersionSchema>;

// ---------------------------------------------------------------------------
// 2. consent_events
// ---------------------------------------------------------------------------
export const ConsentEventCreateSchema = z.object({
  user_id: UUID,
  source_product: SourceProduct,
  event_type: ConsentEventType,
  policy_version_id: UUID,
  consent_scope: z.record(z.unknown()).default({}),
  ip_address: z.string().nullable().optional(),
  user_agent: z.string().nullable().optional(),
});
export type ConsentEventCreate = z.infer<typeof ConsentEventCreateSchema>;

export const ConsentEventSchema = ConsentEventCreateSchema.extend({
  id: UUID,
  created_at: ISODateTime,
});
export type ConsentEvent = z.infer<typeof ConsentEventSchema>;

// ---------------------------------------------------------------------------
// 3. automated_decision_log
// ---------------------------------------------------------------------------
export const AutomatedDecisionCreateSchema = z.object({
  user_id: UUID,
  source_product: SourceProduct,
  decision_type: z.string().min(1),
  decision_output: z.record(z.unknown()),
  algorithm_version: z.string().min(1),
  model_inputs_hash: z.string().nullable().optional(),
  explanation_text: z.string().nullable().optional(),
  human_reviewable: z.boolean().default(true),
});
export type AutomatedDecisionCreate = z.infer<typeof AutomatedDecisionCreateSchema>;

export const AutomatedDecisionSchema = AutomatedDecisionCreateSchema.extend({
  id: UUID,
  created_at: ISODateTime,
});
export type AutomatedDecision = z.infer<typeof AutomatedDecisionSchema>;

// ---------------------------------------------------------------------------
// 4. human_review_requests
// ---------------------------------------------------------------------------
export const HumanReviewRequestCreateSchema = z.object({
  user_id: UUID,
  automated_decision_id: UUID,
  source_product: SourceProduct,
  request_reason: z.string().min(1),
  // requested_at + sla_deadline filled by DB trigger.
});
export type HumanReviewRequestCreate = z.infer<typeof HumanReviewRequestCreateSchema>;

export const HumanReviewRequestSchema = HumanReviewRequestCreateSchema.extend({
  id: UUID,
  requested_at: ISODateTime,
  sla_deadline: ISODateTime,
  status: HumanReviewStatus.default("pending"),
  resolved_at: ISODateTime.nullable().optional(),
  resolution_notes: z.string().nullable().optional(),
  reviewer_user_id: UUID.nullable().optional(),
});
export type HumanReviewRequest = z.infer<typeof HumanReviewRequestSchema>;
