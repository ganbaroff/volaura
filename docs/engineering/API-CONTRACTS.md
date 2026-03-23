# API Contracts — Volaura

**API Base URL:** `https://api.volaura.com/api/v1`
**Version:** 1.0.0
**Last Updated:** 2026-03-22
**Environment:** Production (Railway)

---

## Overview

Volaura API is a RESTful service built with FastAPI (Python 3.11+) on Railway, backed by Supabase PostgreSQL with Row-Level Security (RLS).

**Key Design Principles:**
- All responses wrapped in standard envelope (success/error)
- Paginated responses include metadata
- Authentication via Supabase JWT in `Authorization: Bearer <token>`
- Rate limiting: 100 requests/minute per authenticated user, 10/minute per IP (unauthenticated)
- All timestamps in ISO 8601 format (UTC)
- All payloads UTF-8 encoded
- Error codes are machine-readable; messages are human-readable

---

## Standard Response Envelopes

### Success Response (2xx)
```json
{
  "data": {...},
  "meta": {
    "timestamp": "2026-03-22T14:30:00Z",
    "request_id": "req_abc123def456",
    "version": "1.0.0"
  }
}
```

### Paginated Success Response
```json
{
  "data": [...],
  "meta": {
    "timestamp": "2026-03-22T14:30:00Z",
    "request_id": "req_abc123def456",
    "pagination": {
      "total": 250,
      "page": 1,
      "per_page": 20,
      "pages": 13
    }
  }
}
```

### Error Response (4xx, 5xx)
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "validation_error_detail"
    },
    "request_id": "req_abc123def456"
  }
}
```

---

## Common Query Parameters

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `page` | int | 1 | N/A | Pagination page number (1-indexed) |
| `per_page` | int | 20 | 100 | Items per page |
| `sort_by` | string | `created_at` | N/A | Field name to sort by |
| `sort_order` | enum | `desc` | N/A | `asc` or `desc` |
| `search` | string | — | N/A | Full-text search filter |

---

## Authentication

**Supabase Auth Endpoints** (handled by Supabase, documented for reference):

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/v1/signup` | Magic link signup |
| POST | `/auth/v1/token?grant_type=magiclink` | Verify magic link token |
| POST | `/auth/v1/token?grant_type=refresh_token` | Refresh JWT token |
| GET | `/auth/v1/user` | Get current user metadata |

All FastAPI endpoints (except `/health` and public profiles) require:
```
Authorization: Bearer <jwt_token>
```

JWT is obtained from Supabase, verified in FastAPI via `CurrentUserId` dependency.

---

## Health & System

### GET /api/v1/health
System health check (no auth required).

**Response:** 200 OK
```json
{
  "data": {
    "status": "ok",
    "db": "connected",
    "llm": "available",
    "version": "1.0.0"
  },
  "meta": {
    "timestamp": "2026-03-22T14:30:00Z",
    "request_id": "req_abc123def456"
  }
}
```

| Status Code | Case | Response |
|-------------|------|----------|
| 200 | All systems operational | `"status": "ok"` |
| 503 | DB or LLM unavailable | `"status": "degraded"` or `"status": "down"` |

---

## Profile Endpoints

### GET /api/v1/profiles/me
Fetch authenticated user's full profile.

**Auth:** Required (authenticated user)
**Rate Limit:** 60 req/min

**Response:** 200 OK
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "alice@example.com",
    "phone": "+994-50-123-4567",
    "first_name": "Alice",
    "last_name": "Ismayilova",
    "username": "alice_ismayilova",
    "bio": "Event organizer, English fluent",
    "avatar_url": "https://cdn.volaura.com/avatars/alice_550e8400.jpg",
    "location": {
      "city": "Baku",
      "country": "Azerbaijan"
    },
    "languages": ["az", "en", "ru"],
    "role": "volunteer",
    "verified_at": "2026-03-01T10:00:00Z",
    "created_at": "2026-02-15T08:30:00Z",
    "updated_at": "2026-03-22T14:15:00Z"
  },
  "meta": {...}
}
```

| Status | Case |
|--------|------|
| 200 | Success |
| 401 | Not authenticated |
| 404 | User profile not found (edge case) |

---

### PATCH /api/v1/profiles/me
Update authenticated user's profile.

**Auth:** Required
**Rate Limit:** 30 req/min
**Body Validation:** All fields optional

**Request Body:**
```json
{
  "first_name": "Alice",
  "last_name": "Ismayilova",
  "phone": "+994-50-123-4567",
  "bio": "Updated bio...",
  "languages": ["az", "en", "ru"],
  "location": {
    "city": "Baku",
    "country": "Azerbaijan"
  }
}
```

**Response:** 200 OK (returns updated profile, same schema as GET /profiles/me)

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 400 | `INVALID_PHONE` | Phone format invalid (E.164 required) |
| 400 | `INVALID_LANGUAGES` | Unknown language code |
| 401 | — | Not authenticated |
| 422 | `VALIDATION_ERROR` | Schema validation failed |

---

### GET /api/v1/profiles/{username}
Fetch public profile by username (no auth required).

**Auth:** None
**Rate Limit:** 60 req/min
**Path Params:**
- `username` (string, 3-32 chars, alphanumeric + underscore)

**Response:** 200 OK
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "alice_ismayilova",
    "first_name": "Alice",
    "last_name": "Ismayilova",
    "avatar_url": "https://cdn.volaura.com/avatars/alice_550e8400.jpg",
    "bio": "Event organizer, English fluent",
    "location": {
      "city": "Baku",
      "country": "Azerbaijan"
    },
    "languages": ["az", "en", "ru"],
    "verified_at": "2026-03-01T10:00:00Z",
    "aura_score": 82,
    "aura_badge": "gold"
  },
  "meta": {...}
}
```

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 404 | `PROFILE_NOT_FOUND` | Username does not exist |

---

### POST /api/v1/profiles/me/avatar
Upload user avatar image.

**Auth:** Required
**Rate Limit:** 10 req/min
**Content-Type:** `multipart/form-data`
**File Size Max:** 5 MB
**Formats:** PNG, JPEG, WebP

**Request:**
```
POST /api/v1/profiles/me/avatar HTTP/1.1
Content-Type: multipart/form-data

file=<binary>
```

**Response:** 200 OK
```json
{
  "data": {
    "avatar_url": "https://cdn.volaura.com/avatars/alice_550e8400.jpg",
    "size_bytes": 245000
  },
  "meta": {...}
}
```

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 400 | `FILE_TOO_LARGE` | Max 5MB |
| 400 | `INVALID_FORMAT` | Only PNG, JPEG, WebP accepted |
| 401 | — | Not authenticated |
| 422 | `VALIDATION_ERROR` | No file provided |

---

### DELETE /api/v1/profiles/me
Soft-delete user account (profile hidden, data retained 90 days before hard delete).

**Auth:** Required
**Rate Limit:** 1 req/min

**Request Body (optional):**
```json
{
  "reason": "PRIVACY_CONCERN",
  "feedback": "No longer interested in volunteering"
}
```

**Response:** 204 No Content (on success, body empty)

| Status | Code | Message |
|--------|------|---------|
| 204 | — | Success |
| 400 | `ACCOUNT_ALREADY_DELETED` | Account already soft-deleted |
| 401 | — | Not authenticated |
| 429 | `RATE_LIMITED` | Cannot delete account twice within 24h |

---

## Assessment Endpoints

[[DECISIONS.md#Assessment-Algorithm]] — CAT/IRT implementation details

### POST /api/v1/assessments/start
Create new assessment session.

**Auth:** Required
**Rate Limit:** 5 req/min

**Request Body:**
```json
{
  "competency": "communication",
  "language": "az"
}
```

**Pydantic Model:**
```python
class AssessmentStartRequest(BaseModel):
    competency: Literal[
        "communication",
        "reliability",
        "english_proficiency",
        "leadership",
        "event_performance",
        "tech_literacy",
        "adaptability",
        "empathy_safeguarding"
    ]
    language: Literal["az", "en"]
```

**Response:** 201 Created
```json
{
  "data": {
    "id": "asn_xyz789",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "competency": "communication",
    "language": "az",
    "status": "in_progress",
    "questions_answered": 0,
    "current_theta": 0.0,
    "current_se": 1.0,
    "created_at": "2026-03-22T14:30:00Z",
    "expires_at": "2026-03-22T15:30:00Z"
  },
  "meta": {...}
}
```

| Status | Code | Message |
|--------|------|---------|
| 201 | — | Success |
| 400 | `INVALID_COMPETENCY` | Unknown competency |
| 401 | — | Not authenticated |
| 422 | `VALIDATION_ERROR` | Missing required fields |
| 429 | `RATE_LIMITED` | User has incomplete assessment in progress |

---

### GET /api/v1/assessments/{id}
Fetch assessment details.

**Auth:** Required (can only view own)
**Rate Limit:** 60 req/min
**Path Params:**
- `id` (string, format: `asn_*`)

**Response:** 200 OK
```json
{
  "data": {
    "id": "asn_xyz789",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "competency": "communication",
    "language": "az",
    "status": "in_progress",
    "questions_answered": 3,
    "current_theta": 0.25,
    "current_se": 0.85,
    "completion_percentage": 45,
    "created_at": "2026-03-22T14:30:00Z",
    "expires_at": "2026-03-22T15:30:00Z"
  },
  "meta": {...}
}
```

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 401 | — | Not authenticated |
| 403 | `FORBIDDEN` | Cannot view other user's assessment |
| 404 | `ASSESSMENT_NOT_FOUND` | ID does not exist |
| 410 | `ASSESSMENT_EXPIRED` | Session expired (> 60 min inactive) |

---

### GET /api/v1/assessments/{id}/next-question
Get next question from CAT algorithm.

**Auth:** Required (can only access own)
**Rate Limit:** 30 req/min
**Path Params:**
- `id` (string, format: `asn_*`)

**Response:** 200 OK
```json
{
  "data": {
    "question_id": "q_comm_042",
    "text": "How do you handle conflict in team settings?",
    "text_az": "Komanda ortamında konflikt necə idarə edirsiniz?",
    "type": "multiple_choice",
    "options": [
      {
        "id": "opt_1",
        "text": "Avoid confrontation",
        "text_az": "Münaqişəni qarşısını almaq"
      },
      {
        "id": "opt_2",
        "text": "Listen and negotiate",
        "text_az": "Dinləmək və müzakirə etmək"
      },
      {
        "id": "opt_3",
        "text": "Delegate to manager",
        "text_az": "Menecerə tapşırmaq"
      }
    ],
    "order": 4
  },
  "meta": {...}
}
```

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success, more questions available |
| 200 | `ASSESSMENT_COMPLETE` | All questions answered, ready to finalize |
| 401 | — | Not authenticated |
| 403 | `FORBIDDEN` | Cannot access other user's assessment |
| 404 | `ASSESSMENT_NOT_FOUND` | ID does not exist |
| 410 | `ASSESSMENT_EXPIRED` | Session expired |

---

### POST /api/v1/assessments/{id}/answers
Submit answer to current question.

**Auth:** Required (own assessment only)
**Rate Limit:** 20 req/min
**Path Params:**
- `id` (string, format: `asn_*`)

**Request Body:**
```json
{
  "question_id": "q_comm_042",
  "selected_option_id": "opt_2",
  "time_spent_seconds": 45,
  "confidence": 0.8
}
```

**Pydantic Model:**
```python
class AnswerSubmissionRequest(BaseModel):
    question_id: str
    selected_option_id: str
    time_spent_seconds: int = Field(ge=1, le=300)
    confidence: float = Field(ge=0.0, le=1.0)
```

**Response:** 200 OK
```json
{
  "data": {
    "assessment_id": "asn_xyz789",
    "question_id": "q_comm_042",
    "selected_option_id": "opt_2",
    "is_correct": true,
    "theta_updated": 0.35,
    "se_updated": 0.75,
    "total_answered": 4,
    "next_question_available": true
  },
  "meta": {...}
}
```

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 400 | `INVALID_OPTION_ID` | Option ID does not belong to this question |
| 400 | `QUESTION_MISMATCH` | Question ID doesn't match current session question |
| 401 | — | Not authenticated |
| 403 | `FORBIDDEN` | Cannot answer for other user's assessment |
| 404 | `ASSESSMENT_NOT_FOUND` | Assessment ID does not exist |
| 410 | `ASSESSMENT_EXPIRED` | Session expired |
| 422 | `VALIDATION_ERROR` | Invalid time_spent_seconds or confidence |

---

### POST /api/v1/assessments/{id}/complete
Finalize assessment and compute AURA contribution.

**Auth:** Required (own only)
**Rate Limit:** 5 req/min
**Path Params:**
- `id` (string, format: `asn_*`)

**Request Body:** Empty

**Response:** 200 OK
```json
{
  "data": {
    "assessment_id": "asn_xyz789",
    "competency": "communication",
    "final_theta": 0.45,
    "final_se": 0.70,
    "score": 78,
    "percentile": 82,
    "aura_points_awarded": 15,
    "completion_time_seconds": 420,
    "questions_count": 8,
    "completed_at": "2026-03-22T14:45:00Z"
  },
  "meta": {...}
}
```

**Pydantic Response Model:**
```python
class AssessmentCompletionResponse(BaseModel):
    assessment_id: str
    competency: str
    final_theta: float
    final_se: float
    score: int
    percentile: int
    aura_points_awarded: int
    completion_time_seconds: int
    questions_count: int
    completed_at: datetime
```

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 400 | `ASSESSMENT_INCOMPLETE` | Not all required answers submitted |
| 400 | `ASSESSMENT_ALREADY_COMPLETED` | Assessment already finalized |
| 401 | — | Not authenticated |
| 403 | `FORBIDDEN` | Cannot complete other user's assessment |
| 404 | `ASSESSMENT_NOT_FOUND` | ID does not exist |
| 410 | `ASSESSMENT_EXPIRED` | Session expired |

---

### GET /api/v1/assessments/history
Fetch user's completed assessments (paginated).

**Auth:** Required
**Rate Limit:** 60 req/min
**Query Params:**
- `page` (default: 1)
- `per_page` (default: 20, max: 100)
- `competency` (optional filter)
- `sort_by` (default: `completed_at`)

**Response:** 200 OK
```json
{
  "data": [
    {
      "assessment_id": "asn_xyz789",
      "competency": "communication",
      "score": 78,
      "percentile": 82,
      "completed_at": "2026-03-22T14:45:00Z",
      "aura_points_awarded": 15
    }
  ],
  "meta": {
    "timestamp": "2026-03-22T14:30:00Z",
    "request_id": "req_abc123def456",
    "pagination": {
      "total": 8,
      "page": 1,
      "per_page": 20,
      "pages": 1
    }
  }
}
```

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 401 | — | Not authenticated |

---

## AURA Score Endpoints

[[DECISIONS.md#AURA-Scoring]] — Score calculation methodology

### GET /api/v1/scores/me
Fetch authenticated user's AURA score and breakdown.

**Auth:** Required
**Rate Limit:** 60 req/min

**Response:** 200 OK
```json
{
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "total_score": 82.5,
    "badge": "gold",
    "percentile": 78,
    "last_updated": "2026-03-22T14:30:00Z",
    "breakdown": {
      "communication": {
        "score": 85,
        "weight": 0.20,
        "weighted_points": 17.0,
        "assessments_count": 2,
        "last_assessed": "2026-03-22T14:45:00Z"
      },
      "reliability": {
        "score": 78,
        "weight": 0.15,
        "weighted_points": 11.7,
        "assessments_count": 1,
        "last_assessed": "2026-03-15T10:20:00Z"
      },
      "english_proficiency": {
        "score": 81,
        "weight": 0.15,
        "weighted_points": 12.15,
        "assessments_count": 1,
        "last_assessed": "2026-03-10T09:00:00Z"
      },
      "leadership": {
        "score": 72,
        "weight": 0.15,
        "weighted_points": 10.8,
        "assessments_count": 1,
        "last_assessed": "2026-02-28T14:30:00Z"
      },
      "event_performance": {
        "score": 88,
        "weight": 0.10,
        "weighted_points": 8.8,
        "attestations_count": 3
      },
      "tech_literacy": {
        "score": 75,
        "weight": 0.10,
        "weighted_points": 7.5,
        "assessments_count": 1,
        "last_assessed": "2026-03-01T11:15:00Z"
      },
      "adaptability": {
        "score": 80,
        "weight": 0.10,
        "weighted_points": 8.0,
        "assessments_count": 2,
        "last_assessed": "2026-03-08T16:45:00Z"
      },
      "empathy_safeguarding": {
        "score": 76,
        "weight": 0.05,
        "weighted_points": 3.8,
        "assessments_count": 1,
        "last_assessed": "2026-03-05T13:20:00Z"
      }
    },
    "trend": "up",
    "trend_change_30_days": 3.5
  },
  "meta": {...}
}
```

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 401 | — | Not authenticated |
| 404 | `SCORE_NOT_FOUND` | User has no assessed competencies yet |

---

### GET /api/v1/scores/{user_id}
Fetch user's public AURA score (no auth required).

**Auth:** None
**Rate Limit:** 60 req/min
**Path Params:**
- `user_id` (UUID format)

**Response:** 200 OK (subset of /scores/me, public data only)
```json
{
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "alice_ismayilova",
    "total_score": 82.5,
    "badge": "gold",
    "percentile": 78,
    "breakdown": {
      "communication": 85,
      "reliability": 78,
      "english_proficiency": 81,
      "leadership": 72,
      "event_performance": 88,
      "tech_literacy": 75,
      "adaptability": 80,
      "empathy_safeguarding": 76
    }
  },
  "meta": {...}
}
```

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 404 | `PROFILE_NOT_FOUND` | User ID does not exist |
| 404 | `SCORE_NOT_FOUND` | User has no assessed competencies |

---

### GET /api/v1/scores/me/history
Fetch user's AURA score history (paginated, monthly).

**Auth:** Required
**Rate Limit:** 60 req/min
**Query Params:**
- `page` (default: 1)
- `per_page` (default: 12, max: 36)
- `start_date` (ISO 8601, optional)
- `end_date` (ISO 8601, optional)

**Response:** 200 OK
```json
{
  "data": [
    {
      "date": "2026-03-22",
      "score": 82.5,
      "badge": "gold",
      "percentile": 78
    },
    {
      "date": "2026-02-22",
      "score": 79.0,
      "badge": "gold",
      "percentile": 75
    }
  ],
  "meta": {
    "pagination": {
      "total": 8,
      "page": 1,
      "per_page": 12,
      "pages": 1
    }
  }
}
```

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 401 | — | Not authenticated |
| 422 | `INVALID_DATE_FORMAT` | start_date or end_date not ISO 8601 |

---

### GET /api/v1/scores/leaderboard
Global AURA leaderboard (paginated).

**Auth:** None
**Rate Limit:** 30 req/min
**Query Params:**
- `page` (default: 1)
- `per_page` (default: 50, max: 100)
- `time_range` (`all_time` | `30_days` | `7_days`, default: `all_time`)

**Response:** 200 OK
```json
{
  "data": [
    {
      "rank": 1,
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "alice_ismayilova",
      "avatar_url": "https://cdn.volaura.com/avatars/alice_550e8400.jpg",
      "score": 94.2,
      "badge": "platinum",
      "change_from_last_month": 2.5
    },
    {
      "rank": 2,
      "user_id": "660e8400-e29b-41d4-a716-446655440001",
      "username": "bob_hasan",
      "avatar_url": "https://cdn.volaura.com/avatars/bob_660e8400.jpg",
      "score": 91.8,
      "badge": "platinum",
      "change_from_last_month": -1.0
    }
  ],
  "meta": {
    "pagination": {
      "total": 1500,
      "page": 1,
      "per_page": 50,
      "pages": 30
    }
  }
}
```

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |

---

### GET /api/v1/scores/leaderboard/{competency}
Leaderboard for single competency (paginated).

**Auth:** None
**Rate Limit:** 30 req/min
**Path Params:**
- `competency` (one of: communication, reliability, english_proficiency, leadership, event_performance, tech_literacy, adaptability, empathy_safeguarding)

**Query Params:**
- `page` (default: 1)
- `per_page` (default: 50, max: 100)

**Response:** 200 OK (same structure as /leaderboard, filtered by competency)

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 400 | `INVALID_COMPETENCY` | Unknown competency |

---

## Event Endpoints

### GET /api/v1/events
List events (filterable, paginated).

**Auth:** None
**Rate Limit:** 60 req/min
**Query Params:**
- `page` (default: 1)
- `per_page` (default: 20, max: 100)
- `location` (string, optional — city or coordinates)
- `date_from` (ISO 8601, optional)
- `date_to` (ISO 8601, optional)
- `min_aura_required` (int 0-100, optional)
- `status` (`upcoming` | `ongoing` | `completed`, optional)
- `search` (string, full-text search)
- `sort_by` (`date_start` | `created_at` | `registrations`, default: `date_start`)

**Response:** 200 OK
```json
{
  "data": [
    {
      "id": "evt_12345",
      "title": "Community Clean-up Drive",
      "title_az": "Cəmiyyət Təmizləmə Kampaniyası",
      "description": "Help clean up parks in Baku",
      "organization_id": "org_67890",
      "organization_name": "Green Baku",
      "location": {
        "city": "Baku",
        "country": "Azerbaijan",
        "latitude": 40.3776,
        "longitude": 49.8930
      },
      "date_start": "2026-04-15T09:00:00Z",
      "date_end": "2026-04-15T12:00:00Z",
      "status": "upcoming",
      "min_aura_required": 40,
      "capacity": 50,
      "registered_count": 23,
      "featured_image": "https://cdn.volaura.com/events/evt_12345.jpg",
      "created_at": "2026-03-01T10:00:00Z"
    }
  ],
  "meta": {
    "pagination": {
      "total": 245,
      "page": 1,
      "per_page": 20,
      "pages": 13
    }
  }
}
```

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 400 | `INVALID_DATE_FORMAT` | date_from or date_to not ISO 8601 |
| 400 | `INVALID_AURA_RANGE` | min_aura_required not 0-100 |

---

### GET /api/v1/events/{id}
Fetch event details.

**Auth:** None
**Rate Limit:** 60 req/min
**Path Params:**
- `id` (string, format: `evt_*`)

**Response:** 200 OK
```json
{
  "data": {
    "id": "evt_12345",
    "title": "Community Clean-up Drive",
    "title_az": "Cəmiyyət Təmizləmə Kampaniyası",
    "description": "Help clean up parks in Baku city center...",
    "description_az": "Baku şəhər mərkəzində...",
    "organization_id": "org_67890",
    "organization_name": "Green Baku",
    "organization_verified": true,
    "location": {
      "city": "Baku",
      "country": "Azerbaijan",
      "address": "Heydar Aliyev Park",
      "latitude": 40.3776,
      "longitude": 49.8930
    },
    "date_start": "2026-04-15T09:00:00Z",
    "date_end": "2026-04-15T12:00:00Z",
    "status": "upcoming",
    "min_aura_required": 40,
    "capacity": 50,
    "registered_count": 23,
    "tags": ["environment", "community", "outdoor"],
    "featured_image": "https://cdn.volaura.com/events/evt_12345.jpg",
    "contact_email": "events@greenbaku.az",
    "contact_phone": "+994-50-123-4567",
    "is_registered": false,
    "rating": 4.6,
    "rating_count": 18,
    "created_at": "2026-03-01T10:00:00Z",
    "updated_at": "2026-03-15T14:30:00Z"
  },
  "meta": {...}
}
```

**Note:** `is_registered` only appears when authenticated; shows current user's registration status.

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 404 | `EVENT_NOT_FOUND` | Event ID does not exist |

---

### POST /api/v1/events/{id}/register
Register authenticated user for event.

**Auth:** Required
**Rate Limit:** 10 req/min
**Path Params:**
- `id` (string, format: `evt_*`)

**Request Body:** Empty

**Response:** 201 Created
```json
{
  "data": {
    "registration_id": "reg_xyz789",
    "event_id": "evt_12345",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "registered_at": "2026-03-22T14:30:00Z",
    "status": "confirmed"
  },
  "meta": {...}
}
```

| Status | Code | Message |
|--------|------|---------|
| 201 | — | Success |
| 400 | `ALREADY_REGISTERED` | User already registered for this event |
| 400 | `AURA_REQUIREMENT_NOT_MET` | User's AURA score below minimum |
| 400 | `EVENT_FULL` | Event capacity reached |
| 400 | `EVENT_EXPIRED` | Event date has passed |
| 401 | — | Not authenticated |
| 404 | `EVENT_NOT_FOUND` | Event ID does not exist |
| 429 | `RATE_LIMITED` | Too many registration attempts |

---

### DELETE /api/v1/events/{id}/register
Unregister authenticated user from event.

**Auth:** Required
**Rate Limit:** 10 req/min
**Path Params:**
- `id` (string, format: `evt_*`)

**Request Body:** Empty

**Response:** 204 No Content

| Status | Code | Message |
|--------|------|---------|
| 204 | — | Success |
| 400 | `NOT_REGISTERED` | User not registered for this event |
| 400 | `EVENT_IN_PROGRESS` | Cannot unregister from ongoing event |
| 401 | — | Not authenticated |
| 404 | `EVENT_NOT_FOUND` | Event ID does not exist |

---

### GET /api/v1/events/my-events
Fetch authenticated user's registered events (paginated).

**Auth:** Required
**Rate Limit:** 60 req/min
**Query Params:**
- `page` (default: 1)
- `per_page` (default: 20, max: 100)
- `status` (`upcoming` | `ongoing` | `completed`, optional)
- `sort_by` (`date_start` | `registered_at`, default: `date_start`)

**Response:** 200 OK
```json
{
  "data": [
    {
      "registration_id": "reg_xyz789",
      "event_id": "evt_12345",
      "title": "Community Clean-up Drive",
      "date_start": "2026-04-15T09:00:00Z",
      "location": {
        "city": "Baku"
      },
      "status": "upcoming",
      "registered_at": "2026-03-22T14:30:00Z",
      "feedback_pending": false
    }
  ],
  "meta": {
    "pagination": {
      "total": 12,
      "page": 1,
      "per_page": 20,
      "pages": 1
    }
  }
}
```

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 401 | — | Not authenticated |

---

## Organization Endpoints

### GET /api/v1/org/me
Fetch authenticated org admin's organization profile.

**Auth:** Required (org_admin role)
**Rate Limit:** 60 req/min

**Response:** 200 OK
```json
{
  "data": {
    "id": "org_67890",
    "name": "Green Baku",
    "description": "Environmental conservation nonprofit",
    "website": "https://greenbaku.az",
    "logo_url": "https://cdn.volaura.com/orgs/org_67890_logo.png",
    "verification_status": "verified",
    "verified_at": "2026-02-01T10:00:00Z",
    "email": "contact@greenbaku.az",
    "phone": "+994-50-123-4567",
    "location": {
      "city": "Baku",
      "country": "Azerbaijan"
    },
    "events_hosted": 12,
    "total_volunteers_engaged": 245,
    "avg_rating": 4.7,
    "admin_user_id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2026-01-15T08:00:00Z"
  },
  "meta": {...}
}
```

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 401 | — | Not authenticated |
| 403 | `FORBIDDEN` | User is not org_admin |
| 404 | `ORG_NOT_FOUND` | Organization not found |

---

### PATCH /api/v1/org/me
Update organization profile (org_admin only).

**Auth:** Required (org_admin)
**Rate Limit:** 30 req/min

**Request Body:**
```json
{
  "name": "Green Baku Initiative",
  "description": "Updated description",
  "website": "https://greenbaku.az",
  "email": "contact@greenbaku.az",
  "phone": "+994-50-987-6543",
  "location": {
    "city": "Baku",
    "country": "Azerbaijan"
  }
}
```

**Response:** 200 OK (returns updated org, same schema as GET /org/me)

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 400 | `INVALID_WEBSITE_URL` | Website URL format invalid |
| 401 | — | Not authenticated |
| 403 | `FORBIDDEN` | User is not org_admin |
| 422 | `VALIDATION_ERROR` | Schema validation failed |

---

### POST /api/v1/org/events
Create new event (org_admin only).

**Auth:** Required (org_admin)
**Rate Limit:** 10 req/min

**Request Body:**
```json
{
  "title": "Community Clean-up Drive",
  "title_az": "Cəmiyyət Təmizləmə Kampaniyası",
  "description": "Help clean up parks in Baku",
  "description_az": "Baku parkları təmizləməyə kömək edin",
  "location": {
    "city": "Baku",
    "country": "Azerbaijan",
    "address": "Heydar Aliyev Park",
    "latitude": 40.3776,
    "longitude": 49.8930
  },
  "date_start": "2026-04-15T09:00:00Z",
  "date_end": "2026-04-15T12:00:00Z",
  "capacity": 50,
  "min_aura_required": 40,
  "contact_email": "events@greenbaku.az",
  "contact_phone": "+994-50-123-4567",
  "tags": ["environment", "community"]
}
```

**Pydantic Model:**
```python
class EventCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    title_az: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=2000)
    description_az: str = Field(min_length=10, max_length=2000)
    location: LocationModel
    date_start: datetime
    date_end: datetime
    capacity: int = Field(ge=1, le=10000)
    min_aura_required: int = Field(ge=0, le=100)
    contact_email: EmailStr
    contact_phone: str
    tags: list[str] = Field(max_items=10)
```

**Response:** 201 Created
```json
{
  "data": {
    "id": "evt_12345",
    "title": "Community Clean-up Drive",
    "organization_id": "org_67890",
    "status": "upcoming",
    "created_at": "2026-03-22T14:30:00Z"
  },
  "meta": {...}
}
```

| Status | Code | Message |
|--------|------|---------|
| 201 | — | Success |
| 400 | `INVALID_DATE_RANGE` | date_end before date_start |
| 400 | `DATE_IN_PAST` | Event date is in the past |
| 401 | — | Not authenticated |
| 403 | `FORBIDDEN` | User is not org_admin |
| 422 | `VALIDATION_ERROR` | Schema validation failed |

---

### PATCH /api/v1/org/events/{id}
Update event (org_admin only, can only update own org's events).

**Auth:** Required (org_admin)
**Rate Limit:** 10 req/min
**Path Params:**
- `id` (string, format: `evt_*`)

**Request Body:** (all fields optional)
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "capacity": 75,
  "min_aura_required": 45,
  "date_start": "2026-04-16T09:00:00Z",
  "date_end": "2026-04-16T12:00:00Z"
}
```

**Response:** 200 OK

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 400 | `CANNOT_MODIFY_PAST_EVENT` | Event date is in the past |
| 400 | `CANNOT_MODIFY_ONGOING_EVENT` | Event is currently ongoing |
| 401 | — | Not authenticated |
| 403 | `FORBIDDEN` | Not org_admin or not event owner |
| 404 | `EVENT_NOT_FOUND` | Event ID does not exist |

---

### DELETE /api/v1/org/events/{id}
Cancel event (org_admin only).

**Auth:** Required (org_admin)
**Rate Limit:** 5 req/min
**Path Params:**
- `id` (string, format: `evt_*`)

**Request Body:**
```json
{
  "cancellation_reason": "Unforeseen circumstances"
}
```

**Response:** 204 No Content

| Status | Code | Message |
|--------|------|---------|
| 204 | — | Success |
| 400 | `CANNOT_CANCEL_COMPLETED_EVENT` | Event has already completed |
| 401 | — | Not authenticated |
| 403 | `FORBIDDEN` | Not org_admin or not event owner |
| 404 | `EVENT_NOT_FOUND` | Event ID does not exist |

Registered volunteers receive notification of cancellation.

---

### GET /api/v1/org/volunteers/search
Search volunteer pool by AURA score and competencies (org_admin only).

**Auth:** Required (org_admin)
**Rate Limit:** 10 req/min
**Query Params:**
- `page` (default: 1)
- `per_page` (default: 50, max: 100)
- `min_aura_score` (int 0-100, optional)
- `competency` (optional, filter by assessed competency)
- `location` (optional, city name)
- `search` (optional, full-text on name/username)
- `sort_by` (`aura_score` | `verified_at`, default: `aura_score`)

**Response:** 200 OK
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "alice_ismayilova",
      "first_name": "Alice",
      "last_name": "Ismayilova",
      "aura_score": 82,
      "badge": "gold",
      "location": {
        "city": "Baku"
      },
      "verified_at": "2026-03-01T10:00:00Z",
      "top_competencies": [
        {
          "name": "communication",
          "score": 85
        },
        {
          "name": "event_performance",
          "score": 88
        }
      ]
    }
  ],
  "meta": {
    "pagination": {
      "total": 342,
      "page": 1,
      "per_page": 50,
      "pages": 7
    }
  }
}
```

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 401 | — | Not authenticated |
| 403 | `FORBIDDEN` | User is not org_admin |

---

### POST /api/v1/org/volunteers/request
Send volunteer request to user (org_admin only).

**Auth:** Required (org_admin)
**Rate Limit:** 20 req/min

**Request Body:**
```json
{
  "volunteer_user_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_id": "evt_12345",
  "message": "We'd love to have you at our cleanup event!"
}
```

**Response:** 201 Created
```json
{
  "data": {
    "request_id": "vreq_abc123",
    "volunteer_user_id": "550e8400-e29b-41d4-a716-446655440000",
    "organization_id": "org_67890",
    "event_id": "evt_12345",
    "status": "pending",
    "sent_at": "2026-03-22T14:30:00Z"
  },
  "meta": {...}
}
```

Volunteer receives in-app notification and email.

| Status | Code | Message |
|--------|------|---------|
| 201 | — | Success |
| 400 | `VOLUNTEER_ALREADY_REGISTERED` | Volunteer already registered for event |
| 400 | `INVALID_VOLUNTEER_ID` | Volunteer user ID does not exist |
| 401 | — | Not authenticated |
| 403 | `FORBIDDEN` | User is not org_admin |
| 404 | `EVENT_NOT_FOUND` | Event ID does not exist |

---

### POST /api/v1/org/volunteers/{id}/attest
Attest volunteer competency after event (org_admin only).

**Auth:** Required (org_admin)
**Rate Limit:** 20 req/min
**Path Params:**
- `id` (UUID, volunteer user_id)

**Request Body:**
```json
{
  "event_id": "evt_12345",
  "competencies": [
    {
      "competency": "event_performance",
      "score": 90,
      "comment": "Excellent coordination and execution"
    },
    {
      "competency": "reliability",
      "score": 85,
      "comment": "Arrived on time, completed all tasks"
    }
  ]
}
```

**Pydantic Model:**
```python
class CompetencyAttestation(BaseModel):
    competency: str
    score: int = Field(ge=0, le=100)
    comment: str = Field(max_length=500)

class AttestationRequest(BaseModel):
    event_id: str
    competencies: list[CompetencyAttestation]
```

**Response:** 201 Created
```json
{
  "data": {
    "attestation_id": "att_xyz789",
    "volunteer_user_id": "550e8400-e29b-41d4-a716-446655440000",
    "organization_id": "org_67890",
    "event_id": "evt_12345",
    "competencies_attested": 2,
    "aura_points_awarded": 8,
    "created_at": "2026-03-22T14:30:00Z"
  },
  "meta": {...}
}
```

Volunteer receives notification of attestation. AURA score updated asynchronously.

| Status | Code | Message |
|--------|------|---------|
| 201 | — | Success |
| 400 | `VOLUNTEER_NOT_REGISTERED` | Volunteer did not register for this event |
| 400 | `INVALID_COMPETENCY` | Unknown competency name |
| 400 | `ALREADY_ATTESTED` | This volunteer already attested for this event |
| 401 | — | Not authenticated |
| 403 | `FORBIDDEN` | User is not org_admin or not event owner |
| 404 | `EVENT_NOT_FOUND` | Event ID does not exist |
| 404 | `VOLUNTEER_NOT_FOUND` | Volunteer user ID does not exist |

---

### POST /api/v1/org/events/{id}/rate/{user_id}
Rate volunteer event performance (org_admin only).

**Auth:** Required (org_admin)
**Rate Limit:** 20 req/min
**Path Params:**
- `id` (string, format: `evt_*` — event_id)
- `user_id` (UUID — volunteer user_id)

**Request Body:**
```json
{
  "rating": 5,
  "review": "Excellent volunteer, very reliable and helpful"
}
```

**Pydantic Model:**
```python
class EventRatingRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    review: str = Field(max_length=1000)
```

**Response:** 201 Created
```json
{
  "data": {
    "rating_id": "rating_xyz",
    "event_id": "evt_12345",
    "volunteer_user_id": "550e8400-e29b-41d4-a716-446655440000",
    "rating": 5,
    "review": "Excellent volunteer...",
    "organization_id": "org_67890",
    "created_at": "2026-03-22T14:30:00Z"
  },
  "meta": {...}
}
```

Volunteer receives notification of review.

| Status | Code | Message |
|--------|------|---------|
| 201 | — | Success |
| 400 | `VOLUNTEER_NOT_REGISTERED` | Volunteer did not register for event |
| 400 | `EVENT_NOT_COMPLETED` | Cannot rate event before it completes |
| 400 | `ALREADY_RATED` | Organization already rated this volunteer for this event |
| 401 | — | Not authenticated |
| 403 | `FORBIDDEN` | User is not org_admin or not event owner |
| 404 | `EVENT_NOT_FOUND` | Event ID does not exist |
| 404 | `VOLUNTEER_NOT_FOUND` | Volunteer user ID does not exist |

---

## Verification Endpoints

### GET /api/v1/verifications/me
Fetch authenticated user's verification status per competency.

**Auth:** Required
**Rate Limit:** 60 req/min

**Response:** 200 OK
```json
{
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "competencies": [
      {
        "competency": "communication",
        "verified": true,
        "verified_at": "2026-03-10T14:30:00Z",
        "verified_by": "assessment",
        "verifiers_count": 3
      },
      {
        "competency": "event_performance",
        "verified": true,
        "verified_by": "attestation",
        "attestations_count": 2,
        "last_attested": "2026-03-15T10:00:00Z"
      },
      {
        "competency": "leadership",
        "verified": true,
        "verified_by": "peer",
        "verifiers": [
          {
            "verifier_id": "550e8400-e29b-41d4-a716-446655440001",
            "verifier_username": "bob_hasan",
            "verified_at": "2026-02-20T09:15:00Z"
          }
        ]
      },
      {
        "competency": "tech_literacy",
        "verified": false,
        "requested_peer_verifications": 1,
        "pending_from": [
          {
            "requester_id": "550e8400-e29b-41d4-a716-446655440002",
            "requester_username": "charlie_mahmud"
          }
        ]
      }
    ]
  },
  "meta": {...}
}
```

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 401 | — | Not authenticated |

---

### POST /api/v1/verifications/peer/request
Request peer verification for a competency.

**Auth:** Required
**Rate Limit:** 10 req/min

**Request Body:**
```json
{
  "target_user_id": "550e8400-e29b-41d4-a716-446655440000",
  "competency": "leadership",
  "message": "Could you verify my leadership abilities based on our recent project?"
}
```

**Pydantic Model:**
```python
class PeerVerificationRequest(BaseModel):
    target_user_id: UUID
    competency: str
    message: str = Field(max_length=500)
```

**Response:** 201 Created
```json
{
  "data": {
    "request_id": "pverreq_xyz789",
    "requestor_user_id": "550e8400-e29b-41d4-a716-446655440000",
    "target_user_id": "550e8400-e29b-41d4-a716-446655440001",
    "competency": "leadership",
    "status": "pending",
    "requested_at": "2026-03-22T14:30:00Z"
  },
  "meta": {...}
}
```

Target user receives notification.

| Status | Code | Message |
|--------|------|---------|
| 201 | — | Success |
| 400 | `INVALID_COMPETENCY` | Unknown competency |
| 400 | `ALREADY_VERIFIED_BY_USER` | Target user already verified this competency for requester |
| 400 | `DUPLICATE_REQUEST` | Request already pending with this user for this competency |
| 400 | `CANNOT_VERIFY_SELF` | Cannot request verification from yourself |
| 401 | — | Not authenticated |
| 404 | `TARGET_USER_NOT_FOUND` | Target user ID does not exist |

---

### POST /api/v1/verifications/peer/{id}/verify
Submit peer verification for another user's competency.

**Auth:** Required
**Rate Limit:** 20 req/min
**Path Params:**
- `id` (string, format: `pverreq_*` — peer_verification_request_id)

**Request Body:**
```json
{
  "verified": true,
  "comment": "Alice demonstrated excellent leadership during our project"
}
```

**Pydantic Model:**
```python
class PeerVerificationResponse(BaseModel):
    verified: bool
    comment: str = Field(max_length=500)
```

**Response:** 200 OK
```json
{
  "data": {
    "verification_id": "pver_abc123",
    "request_id": "pverreq_xyz789",
    "verifier_user_id": "550e8400-e29b-41d4-a716-446655440001",
    "target_user_id": "550e8400-e29b-41d4-a716-446655440000",
    "competency": "leadership",
    "verified": true,
    "comment": "Alice demonstrated...",
    "verified_at": "2026-03-22T14:30:00Z"
  },
  "meta": {...}
}
```

Target user receives notification. If verified, competency marked as peer-verified.

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 400 | `REQUEST_ALREADY_RESPONDED` | Already responded to this request |
| 401 | — | Not authenticated |
| 403 | `FORBIDDEN` | Not the intended verifier |
| 404 | `REQUEST_NOT_FOUND` | Request ID does not exist or expired |

---

### GET /api/v1/verifications/peer/pending
Fetch pending peer verification requests for authenticated user.

**Auth:** Required
**Rate Limit:** 60 req/min
**Query Params:**
- `page` (default: 1)
- `per_page` (default: 20, max: 100)

**Response:** 200 OK
```json
{
  "data": [
    {
      "request_id": "pverreq_xyz789",
      "requestor_user_id": "550e8400-e29b-41d4-a716-446655440000",
      "requestor_username": "alice_ismayilova",
      "requestor_avatar": "https://cdn.volaura.com/avatars/alice_550e8400.jpg",
      "competency": "leadership",
      "message": "Could you verify my leadership abilities...",
      "requested_at": "2026-03-20T10:00:00Z"
    }
  ],
  "meta": {
    "pagination": {
      "total": 5,
      "page": 1,
      "per_page": 20,
      "pages": 1
    }
  }
}
```

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 401 | — | Not authenticated |

---

## Sharing & Social Endpoints

### GET /api/v1/share/{username}/og-image
Generate Open Graph image for social sharing (no auth).

**Auth:** None
**Rate Limit:** 60 req/min
**Path Params:**
- `username` (string, 3-32 chars)

**Headers Response:**
```
Content-Type: image/png
Cache-Control: public, max-age=86400
```

Returns PNG image (1200x630px) with:
- User's avatar
- First/last name
- AURA score & badge
- Top competency

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Image generated |
| 404 | `PROFILE_NOT_FOUND` | Username does not exist |

---

### GET /api/v1/share/{username}/card/{format}
Generate shareable credential card (no auth).

**Auth:** None
**Rate Limit:** 60 req/min
**Path Params:**
- `username` (string)
- `format` (enum: `linkedin` | `story` | `square`)

**Query Params:**
- `download` (bool, default: false — if true, returns as attachment)

**Response:** 200 OK (returns image or redirect to CDN)
- `linkedin`: 1200x627px
- `story`: 1080x1920px
- `square`: 1080x1080px

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Image generated |
| 400 | `INVALID_FORMAT` | format not in (linkedin, story, square) |
| 404 | `PROFILE_NOT_FOUND` | Username does not exist |

---

### POST /api/v1/share/referral
Generate referral link for inviting others.

**Auth:** Required
**Rate Limit:** 5 req/min

**Request Body:** Empty

**Response:** 201 Created
```json
{
  "data": {
    "referral_code": "ALICE_3F7X9K",
    "referral_url": "https://volaura.com/join?ref=ALICE_3F7X9K",
    "created_at": "2026-03-22T14:30:00Z"
  },
  "meta": {...}
}
```

User can generate multiple codes. Each code links signup to referrer for rewards.

| Status | Code | Message |
|--------|------|---------|
| 201 | — | Success |
| 401 | — | Not authenticated |

---

### GET /api/v1/share/referral/stats
Fetch referral statistics for authenticated user.

**Auth:** Required
**Rate Limit:** 60 req/min

**Response:** 200 OK
```json
{
  "data": {
    "referral_codes": [
      {
        "code": "ALICE_3F7X9K",
        "created_at": "2026-03-22T14:30:00Z",
        "clicks": 42,
        "signups": 8,
        "active_referrals": 6
      }
    ],
    "total_referrals": 14,
    "reward_points_earned": 42,
    "reward_status": "gold_tier"
  },
  "meta": {...}
}
```

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 401 | — | Not authenticated |

---

## Notification Endpoints

### GET /api/v1/notifications
List user's notifications (paginated).

**Auth:** Required
**Rate Limit:** 60 req/min
**Query Params:**
- `page` (default: 1)
- `per_page` (default: 20, max: 100)
- `unread_only` (bool, default: false)
- `type` (optional: `event_registration`, `peer_verification`, `attestation`, `event_invitation`, `rating`, `score_change`)

**Response:** 200 OK
```json
{
  "data": [
    {
      "id": "notif_xyz789",
      "type": "event_invitation",
      "title": "Green Baku invited you to an event",
      "message": "Join us for Community Clean-up Drive on April 15",
      "read": false,
      "data": {
        "organization_name": "Green Baku",
        "event_id": "evt_12345",
        "event_title": "Community Clean-up Drive"
      },
      "created_at": "2026-03-22T14:30:00Z",
      "action_url": "/events/evt_12345"
    }
  ],
  "meta": {
    "pagination": {
      "total": 45,
      "page": 1,
      "per_page": 20,
      "pages": 3
    }
  }
}
```

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 401 | — | Not authenticated |

---

### PATCH /api/v1/notifications/{id}/read
Mark single notification as read.

**Auth:** Required
**Rate Limit:** 20 req/min
**Path Params:**
- `id` (string, format: `notif_*`)

**Request Body:** Empty

**Response:** 204 No Content

| Status | Code | Message |
|--------|------|---------|
| 204 | — | Success |
| 401 | — | Not authenticated |
| 403 | `FORBIDDEN` | Cannot mark other user's notification as read |
| 404 | `NOTIFICATION_NOT_FOUND` | Notification ID does not exist |

---

### POST /api/v1/notifications/read-all
Mark all notifications as read.

**Auth:** Required
**Rate Limit:** 5 req/min

**Request Body:** Empty

**Response:** 200 OK
```json
{
  "data": {
    "marked_as_read_count": 12
  },
  "meta": {...}
}
```

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 401 | — | Not authenticated |

---

### GET /api/v1/notifications/unread-count
Get count of unread notifications.

**Auth:** Required
**Rate Limit:** 60 req/min

**Response:** 200 OK
```json
{
  "data": {
    "unread_count": 7
  },
  "meta": {...}
}
```

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 401 | — | Not authenticated |

---

## Admin Endpoints

[[DECISIONS.md#Admin-Features]] — Admin role access control

### GET /api/v1/admin/users
List all users (platform_admin only, paginated, searchable).

**Auth:** Required (platform_admin role)
**Rate Limit:** 30 req/min
**Query Params:**
- `page` (default: 1)
- `per_page` (default: 50, max: 100)
- `search` (optional, by email/username/name)
- `role` (optional filter: `volunteer` | `org_admin` | `platform_admin`)
- `verified_only` (bool, default: false)
- `sort_by` (default: `created_at`)

**Response:** 200 OK
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "alice@example.com",
      "username": "alice_ismayilova",
      "first_name": "Alice",
      "last_name": "Ismayilova",
      "role": "volunteer",
      "verified_at": "2026-03-01T10:00:00Z",
      "aura_score": 82,
      "assessments_count": 3,
      "created_at": "2026-02-15T08:30:00Z",
      "last_login": "2026-03-21T14:15:00Z"
    }
  ],
  "meta": {
    "pagination": {
      "total": 5432,
      "page": 1,
      "per_page": 50,
      "pages": 109
    }
  }
}
```

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 401 | — | Not authenticated |
| 403 | `FORBIDDEN` | User is not platform_admin |

---

### PATCH /api/v1/admin/users/{id}/role
Change user role (platform_admin only).

**Auth:** Required (platform_admin)
**Rate Limit:** 10 req/min
**Path Params:**
- `id` (UUID, user_id)

**Request Body:**
```json
{
  "role": "org_admin"
}
```

**Response:** 200 OK
```json
{
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "previous_role": "volunteer",
    "new_role": "org_admin",
    "updated_at": "2026-03-22T14:30:00Z"
  },
  "meta": {...}
}
```

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 400 | `INVALID_ROLE` | Role not in (volunteer, org_admin, platform_admin) |
| 401 | — | Not authenticated |
| 403 | `FORBIDDEN` | User is not platform_admin |
| 404 | `USER_NOT_FOUND` | User ID does not exist |

---

### GET /api/v1/admin/questions
List all assessment questions (platform_admin only).

**Auth:** Required (platform_admin)
**Rate Limit:** 30 req/min
**Query Params:**
- `page` (default: 1)
- `per_page` (default: 50, max: 100)
- `competency` (optional filter)
- `difficulty` (optional: `easy` | `medium` | `hard`)
- `search` (optional, full-text)

**Response:** 200 OK
```json
{
  "data": [
    {
      "id": "q_comm_042",
      "text": "How do you handle conflict in team settings?",
      "text_az": "Komanda ortamında konflikt necə idarə edirsiniz?",
      "competency": "communication",
      "difficulty": "medium",
      "a_param": -0.8,
      "b_param": 0.5,
      "c_param": 0.2,
      "created_at": "2026-01-10T08:00:00Z",
      "updated_at": "2026-03-15T10:30:00Z",
      "times_used": 342
    }
  ],
  "meta": {
    "pagination": {
      "total": 127,
      "page": 1,
      "per_page": 50,
      "pages": 3
    }
  }
}
```

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 401 | — | Not authenticated |
| 403 | `FORBIDDEN` | User is not platform_admin |

---

### POST /api/v1/admin/questions
Create new assessment question (platform_admin only).

**Auth:** Required (platform_admin)
**Rate Limit:** 10 req/min

**Request Body:**
```json
{
  "text": "How do you prioritize tasks?",
  "text_az": "Tapşırıqları necə prioritetləndirirsiniz?",
  "competency": "reliability",
  "difficulty": "medium",
  "a_param": -0.75,
  "b_param": 0.45,
  "c_param": 0.15,
  "options": [
    {
      "text": "List all tasks and order by deadline",
      "text_az": "Bütün tapşırıqları sıralamaq..."
    },
    {
      "text": "Focus only on urgent items",
      "text_az": "Yalnız acil məsələlərə fokus..."
    }
  ]
}
```

**Pydantic Model:**
```python
class OptionModel(BaseModel):
    text: str = Field(min_length=5, max_length=200)
    text_az: str = Field(min_length=5, max_length=200)

class QuestionCreateRequest(BaseModel):
    text: str = Field(min_length=10, max_length=500)
    text_az: str = Field(min_length=10, max_length=500)
    competency: str
    difficulty: Literal["easy", "medium", "hard"]
    a_param: float = Field(ge=-3.0, le=3.0)
    b_param: float = Field(ge=-3.0, le=3.0)
    c_param: float = Field(ge=0.0, le=1.0)
    options: list[OptionModel] = Field(min_items=2, max_items=5)
```

**Response:** 201 Created
```json
{
  "data": {
    "id": "q_rel_089",
    "competency": "reliability",
    "created_at": "2026-03-22T14:30:00Z"
  },
  "meta": {...}
}
```

| Status | Code | Message |
|--------|------|---------|
| 201 | — | Success |
| 400 | `INVALID_COMPETENCY` | Unknown competency |
| 400 | `INVALID_DIFFICULTY` | difficulty not in (easy, medium, hard) |
| 401 | — | Not authenticated |
| 403 | `FORBIDDEN` | User is not platform_admin |
| 422 | `VALIDATION_ERROR` | Schema validation failed |

---

### PATCH /api/v1/admin/questions/{id}
Update assessment question (platform_admin only).

**Auth:** Required (platform_admin)
**Rate Limit:** 10 req/min
**Path Params:**
- `id` (string, format: `q_*`)

**Request Body:** (all fields optional)
```json
{
  "text": "Updated question text",
  "difficulty": "hard",
  "a_param": -0.9
}
```

**Response:** 200 OK

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 400 | `CANNOT_MODIFY_PUBLISHED_QUESTION` | Question has been used 50+ times |
| 401 | — | Not authenticated |
| 403 | `FORBIDDEN` | User is not platform_admin |
| 404 | `QUESTION_NOT_FOUND` | Question ID does not exist |

---

### DELETE /api/v1/admin/questions/{id}
Soft-delete assessment question (platform_admin only).

**Auth:** Required (platform_admin)
**Rate Limit:** 5 req/min
**Path Params:**
- `id` (string, format: `q_*`)

**Request Body:** Empty

**Response:** 204 No Content

| Status | Code | Message |
|--------|------|---------|
| 204 | — | Success |
| 400 | `CANNOT_DELETE_PUBLISHED_QUESTION` | Question actively used in assessments |
| 401 | — | Not authenticated |
| 403 | `FORBIDDEN` | User is not platform_admin |
| 404 | `QUESTION_NOT_FOUND` | Question ID does not exist |

---

### POST /api/v1/admin/org/{id}/verify
Verify organization (platform_admin only).

**Auth:** Required (platform_admin)
**Rate Limit:** 10 req/min
**Path Params:**
- `id` (string, format: `org_*` — organization_id)

**Request Body:**
```json
{
  "verified": true,
  "notes": "Documentation verified. Nonprofit status confirmed."
}
```

**Response:** 200 OK
```json
{
  "data": {
    "organization_id": "org_67890",
    "verification_status": "verified",
    "verified_at": "2026-03-22T14:30:00Z"
  },
  "meta": {...}
}
```

Org admin receives notification.

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 400 | `ORG_ALREADY_VERIFIED` | Organization already verified |
| 401 | — | Not authenticated |
| 403 | `FORBIDDEN` | User is not platform_admin |
| 404 | `ORG_NOT_FOUND` | Organization ID does not exist |

---

### GET /api/v1/admin/analytics
Platform analytics dashboard data (platform_admin only).

**Auth:** Required (platform_admin)
**Rate Limit:** 5 req/min
**Query Params:**
- `start_date` (ISO 8601, optional, default: 30 days ago)
- `end_date` (ISO 8601, optional, default: today)

**Response:** 200 OK
```json
{
  "data": {
    "summary": {
      "total_users": 5432,
      "verified_users": 3421,
      "volunteer_signups_this_month": 245,
      "organizations_count": 78,
      "verified_organizations": 45
    },
    "assessments": {
      "total_completed": 18923,
      "completed_this_month": 2341,
      "avg_completion_time_seconds": 480,
      "avg_score": 75.2
    },
    "events": {
      "total_events": 412,
      "upcoming_events": 89,
      "completed_events": 198,
      "total_registrations": 8932,
      "avg_event_rating": 4.6
    },
    "engagement": {
      "daily_active_users": 1240,
      "weekly_active_users": 3421,
      "monthly_active_users": 4156,
      "avg_session_duration_minutes": 12.5
    },
    "trending": {
      "top_competency": "communication",
      "most_popular_event_type": "environment",
      "growth_rate_percent": 8.5
    },
    "period": {
      "start_date": "2026-02-22",
      "end_date": "2026-03-22"
    }
  },
  "meta": {...}
}
```

| Status | Code | Message |
|--------|------|---------|
| 200 | — | Success |
| 401 | — | Not authenticated |
| 403 | `FORBIDDEN` | User is not platform_admin |

---

## Rate Limiting

All endpoints follow:
- **Authenticated users:** 100 requests/minute (per user)
- **Unauthenticated (public endpoints):** 10 requests/minute (per IP)
- **Specific tight limits:** Listed per endpoint (e.g., assessment start: 5 req/min)

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1711190400
```

When limit exceeded:
```
HTTP 429 Too Many Requests

{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Reset at 2026-03-22T15:00:00Z",
    "request_id": "req_abc123def456"
  }
}
```

---

## Error Codes Reference

| Code | HTTP | Description |
|------|------|-------------|
| `INVALID_REQUEST` | 400 | Malformed request |
| `VALIDATION_ERROR` | 422 | Schema validation failed |
| `UNAUTHORIZED` | 401 | Missing/invalid JWT token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource already exists |
| `RATE_LIMITED` | 429 | Rate limit exceeded |
| `INTERNAL_SERVER_ERROR` | 500 | Server error (rare) |
| `SERVICE_UNAVAILABLE` | 503 | DB/LLM unavailable |

Specific error codes documented per endpoint.

---

## SDK & Client Generation

**Frontend API Types & Hooks:**
```bash
pnpm generate:api
```

This generates TypeScript types + TanStack Query hooks from `/openapi.json`:
```typescript
import { getProfileMe, usePatchProfileMe } from "@/lib/api/generated";
```

**OpenAPI Schema:**
```
GET https://api.volaura.com/openapi.json
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-22 | Initial release |

---

## Contact & Support

**API Support:** api-support@volaura.com
**Status Page:** https://status.volaura.com
**Docs:** https://docs.volaura.com
