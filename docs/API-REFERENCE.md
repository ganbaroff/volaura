# Volaura API Reference

**Cross-references:** [[adr/ADR-001-system-architecture]] | [[adr/ADR-003-auth-verification]] | [[adr/ADR-004-assessment-engine]] | [[adr/ADR-005-aura-scoring]] | [[MINDSHIFT-INTEGRATION-SPEC]] | [[LIFE-SIMULATOR-INTEGRATION-SPEC]]

**Base URL:** `https://volauraapi-production.up.railway.app`

**Authentication:** Bearer token in `Authorization` header. Obtain via `POST /api/auth/login` or `POST /api/auth/register`.

**Response format:** All responses use `{ data, meta }` envelope or direct Pydantic models. Errors return `{ detail: { code, message } }`.

**Compatibility note:** Some route names and identifiers still use legacy `volunteer` / `volunteer_id` naming. These are compatibility-preserved API names, not product positioning. User-facing meaning is professional/talent profile unless the route explicitly handles event participation.

**Global limits:** 1 MB max request body. CORS whitelist enforced (no wildcards in production).

---

## Health

No prefix. Public.

| Method | Path | Auth | Rate Limit | Request Body | Response | Description |
|--------|------|------|------------|--------------|----------|-------------|
| GET | `/health` | No | - | - | `{ status, version, database, llm_configured, supabase_project_ref }` | DB connectivity + LLM config check |

---

## Auth

Prefix: `/api/auth`

| Method | Path | Auth | Rate Limit | Request Body | Response | Description |
|--------|------|------|------------|--------------|----------|-------------|
| GET | `/api/auth/signup-status` | No | - | - | `{ open_signup: bool }` | Check if open registration is enabled |
| POST | `/api/auth/validate-invite` | No | 5/min | `{ invite_code }` | `{ valid: bool }` | Validate beta invite code (constant-time) |
| POST | `/api/auth/register` | No | 5/min | `{ email, password, username, display_name? }` | `{ access_token, token_type, expires_in, user_id }` | Register new account |
| POST | `/api/auth/login` | No | 5/min | `{ email, password }` | `{ access_token, token_type, expires_in, user_id }` | Login with credentials |
| GET | `/api/auth/me` | Yes | 60/min | - | `{ user_id, profile }` | Get current user from JWT |
| DELETE | `/api/auth/me` | Yes | 5/min | - | `{ message }` | Permanently delete account (GDPR) |
| POST | `/api/auth/logout` | Yes | 5/min | - | `{ message }` | Revoke token server-side (all sessions) |

---

## Profiles

Prefix: `/api/profiles`

| Method | Path | Auth | Rate Limit | Request Body | Response | Description |
|--------|------|------|------------|--------------|----------|-------------|
| GET | `/api/profiles/me` | Yes | 60/min | - | `ProfileResponse` | Get own profile |
| POST | `/api/profiles/me` | Yes | 10/min | `{ username, display_name?, bio?, location?, languages?, account_type?, invited_by_org_id? }` | `ProfileResponse` | Create profile (post-registration) |
| PUT | `/api/profiles/me` | Yes | 10/min | Partial profile fields | `ProfileResponse` | Update own profile |
| POST | `/api/profiles/{volunteer_id}/verification-link` | Yes | 10/min | `{ verifier_name, verifier_org?, competency_id }` | `{ id, token, verify_url, expires_at, ... }` | Create verification link (self only) |
| GET | `/api/profiles/public` | Yes (org) | 10/min | Query: `limit`, `offset` | `[DiscoverableVolunteer]` | List org-visible talent profiles (org accounts only) |
| GET | `/api/profiles/{username}` | No | 10/min | - | `PublicProfileResponse` (includes `percentile_rank`) | Get public profile by username |
| POST | `/api/profiles/{username}/view` | Yes | 20/min | - | `204 No Content` | Record org profile view (sends notification to the profile owner) |

---

## AURA Score

Prefix: `/api/aura`

| Method | Path | Auth | Rate Limit | Request Body | Response | Description |
|--------|------|------|------------|--------------|----------|-------------|
| GET | `/api/aura/me` | Yes | 60/min | - | `AuraScoreResponse` (includes `effective_score`) | Get own AURA score |
| GET | `/api/aura/me/explanation` | Yes | 30/hr | - | `AuraExplanationResponse` (per-competency evaluations) | Transparent evaluation logs |
| GET | `/api/aura/me/visibility` | Yes | 60/min | - | `{ visibility }` | Get current visibility setting |
| PATCH | `/api/aura/me/visibility` | Yes | 10/min | `{ visibility: "public"\|"badge_only"\|"hidden" }` | `{ status, visibility }` | Update AURA visibility |
| POST | `/api/aura/me/sharing` | Yes | 10/min | `{ org_id, action: "grant"\|"revoke", permission_type }` | `{ status, org_id, permission_type }` | Grant/revoke org sharing permission |
| GET | `/api/aura/{volunteer_id}` | No | 10/min | - | `AuraScoreResponse` | Get any public AURA score |

---

## Assessment

Prefix: `/api/assessment`

| Method | Path | Auth | Rate Limit | Request Body | Response | Description |
|--------|------|------|------------|--------------|----------|-------------|
| POST | `/api/assessment/start` | Yes | 3/hr | `{ competency_slug, role_level? }` | `SessionOut` (session_id, first question, CAT state) | Start adaptive assessment session |
| POST | `/api/assessment/answer` | Yes | 60/hr | `{ session_id, question_id, answer, response_time_ms }` | `AnswerFeedback` (next question, session state) | Submit answer, get next question |
| POST | `/api/assessment/complete/{session_id}` | Yes | 10/hr | - | `AssessmentResultOut` (score, badge, gaming flags) | Finalize session, compute AURA |
| GET | `/api/assessment/results/{session_id}` | Yes | 10/hr | - | `AssessmentResultOut` | Retrieve results for completed session |
| POST | `/api/assessment/{session_id}/coaching` | Yes | 30/hr | - | `CoachingResponse` (3 personalized tips via Gemini) | Generate coaching tips (cached) |
| GET | `/api/assessment/info/{competency_slug}` | Yes | 10/min | - | `AssessmentInfoOut` (name, time estimate, retake eligibility) | Pre-assessment metadata |
| GET | `/api/assessment/results/{session_id}/questions` | Yes | 10/min | - | `QuestionBreakdownOut` (per-question difficulty, correctness) | Per-question breakdown |
| GET | `/api/assessment/verify/{session_id}` | No | 10/min | - | `PublicVerificationOut` (competency, score, badge, date) | Public badge verification (LinkedIn click-through) |

**Anti-gaming:** 30-min rapid-restart cooldown. 7-day retest cooldown per competency. Server-side timing. 20/day LLM evaluation cap per user.

---

## Events

Prefix: `/api/events`

| Method | Path | Auth | Rate Limit | Request Body | Response | Description |
|--------|------|------|------------|--------------|----------|-------------|
| GET | `/api/events` | No | 10/min | Query: `status?`, `limit`, `offset` | `[EventResponse]` | List public open events |
| GET | `/api/events/{event_id}` | No | 10/min | - | `EventResponse` | Get single event |
| POST | `/api/events` | Yes (org) | 10/min | `{ title, description, start_date, end_date, capacity?, ... }` | `EventResponse` | Create event (org owner only) |
| PUT | `/api/events/{event_id}` | Yes (org) | 10/min | Partial event fields | `EventResponse` | Update event (org owner only) |
| DELETE | `/api/events/{event_id}` | Yes (org) | 10/min | - | `204` | Cancel event (soft delete, org owner only) |
| POST | `/api/events/{event_id}/register` | Yes | 10/min | - | `RegistrationResponse` | Register for event |
| POST | `/api/events/{event_id}/checkin` | Yes (coordinator) | 10/min | `{ check_in_code }` | `RegistrationResponse` | Check in participant via QR code |
| POST | `/api/events/{event_id}/rate/coordinator` | Yes (coordinator) | 10/min | `{ registration_id, rating: 1-5, feedback? }` | `RegistrationResponse` | Coordinator rates participant performance (updates AURA) |
| POST | `/api/events/{event_id}/rate/volunteer` | Yes | 10/min | `{ rating: 1-5, feedback? }` | `RegistrationResponse` | Participant rates the event experience |
| GET | `/api/events/{event_id}/registrations` | Yes (org) | 10/min | - | `[RegistrationResponse]` | List registrations (org owner only) |
| GET | `/api/events/{event_id}/attendees` | Yes (org) | 10/min | - | `[EventAttendeeRow]` (profile + AURA joined) | Enriched attendee list (org owner only) |
| GET | `/api/events/my/registrations` | Yes | 60/min | - | `[RegistrationResponse]` | List own registrations |

---

## Organizations

Prefix: `/api/organizations`

| Method | Path | Auth | Rate Limit | Request Body | Response | Description |
|--------|------|------|------------|--------------|----------|-------------|
| GET | `/api/organizations` | Yes | 60/min | - | `[OrganizationResponse]` | List all organizations |
| GET | `/api/organizations/me` | Yes | 60/min | - | `OrganizationResponse` | Get own organization |
| POST | `/api/organizations` | Yes | 10/min | `{ name, description?, logo_url?, type?, website? }` | `OrganizationResponse` | Create organization (1 per user) |
| PUT | `/api/organizations/me` | Yes | 10/min | Partial org fields | `OrganizationResponse` | Update own organization |
| GET | `/api/organizations/saved-searches` | Yes (org) | 60/min | - | `[SavedSearchOut]` | List saved talent searches |
| GET | `/api/organizations/{org_id}` | Yes | 60/min | - | `OrganizationResponse` | Get organization by ID |
| GET | `/api/organizations/{org_id}/collective-aura` | Yes (org owner) | 60/min | - | `CollectiveAuraResponse` (count, avg_aura, trend) | Aggregated talent pool AURA metrics |
| GET | `/api/organizations/me/dashboard` | Yes (org) | 60/min | - | `OrgDashboardStats` (completion rate, badge dist, top 5) | Org management dashboard stats |
| GET | `/api/organizations/me/volunteers` | Yes (org) | 10/min | Query: `status?`, `limit`, `offset` | `[OrgVolunteerRow]` | List assigned talent profiles with AURA |
| POST | `/api/organizations/search/volunteers` | Yes (org) | 10/min | `{ query, min_aura?, badge_tier?, languages?, location?, limit, offset }` | `[VolunteerSearchResult]` | Semantic talent search (pgvector + fallback) |
| POST | `/api/organizations/assign-assessments` | Yes (org) | 10/min | `{ volunteer_ids, competency_slugs, deadline_days?, message? }` | `AssignmentResponse` (assigned/skipped counts) | Assign assessments to selected profiles (max 100) |
| POST | `/api/organizations/intro-requests` | Yes (org) | 5/hr | `{ volunteer_id, project_name, timeline?, message }` | `IntroRequestResponse` | Send an introduction request to a selected profile |
| POST | `/api/organizations/saved-searches` | Yes (org) | 10/min | `{ name, filters, notify_on_match? }` | `SavedSearchOut` | Save talent search (max 20 per org) |
| PATCH | `/api/organizations/saved-searches/{search_id}` | Yes (org) | 10/min | `{ name?, notify_on_match? }` | `SavedSearchOut` | Update saved search |
| DELETE | `/api/organizations/saved-searches/{search_id}` | Yes (org) | 10/min | - | `204` | Delete saved search |

---

## Organization Invites

Prefix: `/api/organizations` (shares router with Organizations)

| Method | Path | Auth | Rate Limit | Request Body | Response | Description |
|--------|------|------|------------|--------------|----------|-------------|
| POST | `/api/organizations/{org_id}/invites/bulk` | Yes (org owner) | 2/min | CSV file upload (email required, max 500 rows) | `207` with `BulkInviteResponse` (per-row audit) | Bulk invite participants via CSV |
| GET | `/api/organizations/{org_id}/invites` | Yes (org owner) | 30/min | Query: `status?`, `batch_id?` | `[InviteListResponse]` | List invites for org |
| GET | `/api/organizations/{org_id}/invites/template` | No | 30/min | - | CSV template spec | Download invite template |

---

## Badges (Open Badges 3.0)

Prefix: `/api/badges`

| Method | Path | Auth | Rate Limit | Request Body | Response | Description |
|--------|------|------|------------|--------------|----------|-------------|
| GET | `/api/badges/{volunteer_id}/credential` | No | 10/min | - | W3C Verifiable Credential JSON-LD | Open Badges 3.0 credential (LinkedIn compatible) |
| GET | `/api/badges/issuer` | No | - | - | Issuer profile JSON-LD | Open Badges issuer profile |

---

## Verification

Prefix: `/api/verify`

| Method | Path | Auth | Rate Limit | Request Body | Response | Description |
|--------|------|------|------------|--------------|----------|-------------|
| GET | `/api/verify/{token}` | No | 10/min | - | `VerificationTokenInfo` (profile name, competency) | Validate token, get context for rating UI |
| POST | `/api/verify/{token}` | No | 5/min | `{ rating: 1-5, comment? }` | `SubmitVerificationResponse` | Submit expert rating (single-use token, 7-day expiry) |

---

## Activity

Prefix: `/api/activity`

| Method | Path | Auth | Rate Limit | Request Body | Response | Description |
|--------|------|------|------------|--------------|----------|-------------|
| GET | `/api/activity/me` | Yes | 60/min | Query: `limit`, `offset` | `{ data: [ActivityItem], meta }` | Unified activity feed (assessments, badges, events, signals) |
| GET | `/api/activity/stats/me` | Yes | 60/min | - | `{ data: { events_attended, total_hours, verified_skills, streak_days } }` | Dashboard stats summary |

---

## Analytics

Prefix: `/api/analytics`

| Method | Path | Auth | Rate Limit | Request Body | Response | Description |
|--------|------|------|------------|--------------|----------|-------------|
| POST | `/api/analytics/event` | Yes | 60/min | `{ event_name, properties?, session_id?, locale?, platform? }` | `204` | Ingest frontend analytics event |

---

## Discovery

Prefix: `/api/volunteers`

| Method | Path | Auth | Rate Limit | Request Body | Response | Description |
|--------|------|------|------------|--------------|----------|-------------|
| GET | `/api/volunteers/discovery` | Yes | 10/min | Query: `competency?`, `score_min?`, `role_level?`, `badge_tier?`, `sort_by`, `after_*` cursors, `limit` | `DiscoveryResponse` (cursor-paginated) | Search public talent profiles by competency, score, role, and badge |

**Pagination:** Cursor-based (not offset). Use `next_after_score` + `next_after_id` from `meta` for next page.

---

## Leaderboard

Prefix: `/api/leaderboard`

| Method | Path | Auth | Rate Limit | Request Body | Response | Description |
|--------|------|------|------------|--------------|----------|-------------|
| GET | `/api/leaderboard` | Optional | 10/min | Query: `period` (`weekly`\|`monthly`\|`all_time`), `limit` | `LeaderboardResponse` (entries with rank, score, badge) | Top public AURA profiles (rank >10 anonymized) |
| GET | `/api/leaderboard/me` | Yes | 60/min | - | `{ rank, total_users }` | Current user's leaderboard position |

---

## Notifications

Prefix: `/api/notifications`

| Method | Path | Auth | Rate Limit | Request Body | Response | Description |
|--------|------|------|------------|--------------|----------|-------------|
| GET | `/api/notifications/unread-count` | Yes | 60/min | - | `{ unread_count }` | Unread count for sidebar badge |
| GET | `/api/notifications` | Yes | 60/min | Query: `limit`, `offset` | `NotificationListOut` (notifications, unread_count, total) | List notifications (newest first) |
| PATCH | `/api/notifications/read-all` | Yes | 60/min | - | `{ unread_count: 0 }` | Mark all as read |
| PATCH | `/api/notifications/{notification_id}/read` | Yes | 60/min | - | `NotificationOut` | Mark single notification read |

---

## Stats

Prefix: `/api/stats`

| Method | Path | Auth | Rate Limit | Request Body | Response | Description |
|--------|------|------|------------|--------------|----------|-------------|
| GET | `/api/stats/public` | No | 60/min | - | `{ total_volunteers, total_assessments, total_events, avg_aura_score }` | Platform stats for landing page (legacy metric names preserved for compatibility) |
| GET | `/api/stats/beta-funnel` | Yes (org) | 10/min | - | `BetaFunnelStats` (started, completed, abandoned, rates) | Beta funnel health (org accounts only) |

---

## Subscription

Prefix: `/api/subscription`

| Method | Path | Auth | Rate Limit | Request Body | Response | Description |
|--------|------|------|------------|--------------|----------|-------------|
| GET | `/api/subscription/status` | Yes | 60/min | - | `SubscriptionStatus` (status, trial/sub dates, has_stripe) | Current subscription status (auto-expires stale trials) |
| POST | `/api/subscription/create-checkout` | Yes | 60/min | - | `{ checkout_url }` | Create Stripe Checkout Session (redirect flow) |
| POST | `/api/subscription/webhook` | No (Stripe signature) | 100/min | Stripe event payload | `{ received: true }` | Stripe webhook (signature validated) |

---

## Character (Cross-Product Event Bus)

Prefix: `/api/character`

| Method | Path | Auth | Rate Limit | Request Body | Response | Description |
|--------|------|------|------------|--------------|----------|-------------|
| POST | `/api/character/events` | Yes | 30/min | `{ event_type, payload, source_product }` | `CharacterEventOut` | Store character event (crystal ledger, XP, skills) |
| GET | `/api/character/state` | Yes | 60/min | - | `CharacterStateOut` (crystal_balance, xp, verified_skills, stats) | Computed character state snapshot |
| GET | `/api/character/crystals` | Yes | 60/min | - | `{ user_id, crystal_balance, computed_at }` | Crystal balance only (lightweight) |
| GET | `/api/character/events` | Yes | 60/min | Query: `limit`, `offset` | `[CharacterEventOut]` | Event history (max 200 per request) |

**Crystal events:** `crystal_earned` and `crystal_spent` validate balance, enforce daily caps per source, and use atomic advisory-lock deduction (no TOCTOU race).

---

## BrandedBy (AI Twin)

Prefix: `/api/brandedby`

| Method | Path | Auth | Rate Limit | Request Body | Response | Description |
|--------|------|------|------------|--------------|----------|-------------|
| POST | `/api/brandedby/twins` | Yes | 60/min | `{ display_name, tagline?, photo_url? }` | `AITwinOut` | Create AI Twin (1 per user) |
| GET | `/api/brandedby/twins` | Yes | 60/min | - | `AITwinOut \| null` | Get own AI Twin |
| PATCH | `/api/brandedby/twins/{twin_id}` | Yes | 60/min | Partial twin fields | `AITwinOut` | Update AI Twin (owner only) |
| POST | `/api/brandedby/twins/{twin_id}/refresh-personality` | Yes | 5/min | - | `AITwinOut` | Regenerate personality from character_state via Gemini |
| POST | `/api/brandedby/twins/{twin_id}/activate` | Yes | 60/min | - | `AITwinOut` | Activate twin (requires photo + personality) |
| POST | `/api/brandedby/generations` | Yes | 10/min | `{ twin_id, gen_type, input_text, skip_queue? }` | `GenerationOut` | Request video/audio/chat generation |
| GET | `/api/brandedby/generations` | Yes | 60/min | Query: `limit`, `offset` | `[GenerationOut]` | List generation jobs |
| GET | `/api/brandedby/generations/{gen_id}` | Yes | 60/min | - | `GenerationOut` | Get single generation |

---

## Skills Engine

Prefix: `/api/skills`

| Method | Path | Auth | Rate Limit | Request Body | Response | Description |
|--------|------|------|------------|--------------|----------|-------------|
| GET | `/api/skills/` | No | 60/min | - | `{ data: [{ name, title, endpoint }], meta }` | List available product skills |
| POST | `/api/skills/{skill_name}` | Yes | 30/hr | `{ context?, question?, language? }` | `{ skill, output, model_used }` | Execute skill with user context via LLM |

**Allowed skills:** `aura-coach`, `feed-curator`, `ai-twin-responder`, `content-formatter`, `behavior-pattern-analyzer`.

---

## Tribes (Streaks & Community)

Prefix: `/api/tribes`

| Method | Path | Auth | Rate Limit | Request Body | Response | Description |
|--------|------|------|------------|--------------|----------|-------------|
| GET | `/api/tribes/me` | Yes | 60/min | - | `TribeOut \| null` (members, kudos, renewal status) | Get current active tribe |
| GET | `/api/tribes/me/streak` | Yes | 60/min | - | `TribeStreakOut \| null` (current/longest streak, miss count) | Get personal tribe streak |
| POST | `/api/tribes/me/kudos` | Yes | 5/min | - | `KudosResponse` | Send anonymous kudos to tribe |
| POST | `/api/tribes/opt-out` | Yes | 10/min | - | `OptOutResponse` | Leave tribe silently (streak preserved) |
| POST | `/api/tribes/renew` | Yes | 10/min | - | `RenewalResponse` (all_members_requested flag) | Request 4-week tribe renewal |
| POST | `/api/tribes/join-pool` | Yes | 10/min | - | `TribeMatchPreview` | Opt into tribe matching (daily matching) |
| GET | `/api/tribes/me/pool-status` | Yes | 60/min | - | `{ in_pool, joined_at? }` | Check if in matching pool |

---

## Telegram Webhook

Prefix: `/api/telegram`

| Method | Path | Auth | Rate Limit | Request Body | Response | Description |
|--------|------|------|------------|--------------|----------|-------------|
| POST | `/api/telegram/webhook` | Webhook secret | - | Telegram update JSON | `{ ok: true }` | Receive CEO messages (Telegram Bot API) |
| POST | `/api/telegram/setup-webhook` | Admin secret header | - | - | `{ ok, description }` | Register webhook URL with Telegram |

---

## Admin

Prefix: `/api/admin` (platform admins only -- `is_platform_admin=true`)

| Method | Path | Auth | Rate Limit | Request Body | Response | Description |
|--------|------|------|------------|--------------|----------|-------------|
| GET | `/api/admin/ping` | Admin | 30/min | - | `{ ok: true }` | Admin guard health check |
| GET | `/api/admin/stats` | Admin | 30/min | - | `AdminStatsResponse` (users, orgs, pending approvals, assessments today, avg AURA) | Platform dashboard stats |
| GET | `/api/admin/users` | Admin | 30/min | Query: `limit`, `offset`, `account_type?` | `[AdminUserRow]` | Paginated user list |
| GET | `/api/admin/organizations/pending` | Admin | 30/min | Query: `limit`, `offset` | `[AdminOrgRow]` (with owner username) | Orgs awaiting approval |
| POST | `/api/admin/organizations/{org_id}/approve` | Admin | 30/min | - | `OrgApproveResponse` | Verify organization |
| POST | `/api/admin/organizations/{org_id}/reject` | Admin | 30/min | - | `OrgApproveResponse` | Deactivate organization |

---

## Rate Limit Reference

| Constant | Value | Used For |
|----------|-------|----------|
| `RATE_AUTH` | 5/min | Login, register, logout, delete account |
| `RATE_DEFAULT` | 60/min | General read endpoints |
| `RATE_PROFILE_WRITE` | 10/min | Profile/org mutations |
| `RATE_DISCOVERY` | 10/min | Volunteer search, leaderboard, public profiles |
| `RATE_ASSESSMENT_START` | 3/hr | Start assessment session |
| `RATE_ASSESSMENT_ANSWER` | 60/hr | Submit answer |
| `RATE_ASSESSMENT_COMPLETE` | 10/hr | Complete session, get results |
| `RATE_LLM` | 30/hr | Coaching, skill execution, AURA explanation |

Rate limit key: `IP + SHA256(JWT_token)[:24]`. Returns `429 Too Many Requests` with `Retry-After` header when exceeded.

---

## Error Codes

All errors follow `{ detail: { code: string, message: string } }`.

Common codes: `PROFILE_NOT_FOUND`, `AURA_NOT_FOUND`, `SESSION_NOT_FOUND`, `INVALID_UUID`, `SUBSCRIPTION_REQUIRED` (402), `ORG_REQUIRED` (403), `RETEST_COOLDOWN` (429), `SESSION_EXPIRED` (410), `CONCURRENT_SUBMIT` (409), `INTERNAL_ERROR` (500).
