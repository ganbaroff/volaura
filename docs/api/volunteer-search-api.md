# Volunteer Search API — Contract Document

**Endpoint:** `POST /api/organizations/search/volunteers`
**Auth:** Required (org account only)
**Rate limit:** `RATE_DEFAULT` (60/min)
**Sprint:** 3 — documented 2026-03-28

---

## Request Body

```json
{
  "query": "string",          // required, 1–500 chars. Natural language search query.
                               // e.g. "experienced event coordinator with English"
  "min_aura": 0.0,            // optional float, default 0.0. Minimum AURA total score.
  "badge_tier": null,         // optional string | null. One of: "platinum","gold","silver","bronze"
  "languages": [],            // optional string[]. Filter by spoken languages. e.g. ["az","en"]
  "location": null,           // optional string | null. Partial match on profile location.
  "limit": 10,                // optional int, 1–100, default 10
  "offset": 0                 // optional int, >= 0, default 0
}
```

### Validation rules
- `query`: stripped, min 1 char after trim, max 500
- `badge_tier`: must be exactly `"platinum"`, `"gold"`, `"silver"`, or `"bronze"` — any other value returns 422
- `languages`: post-filter (applied after score/vector search)
- `location`: case-insensitive partial match on profile.location field

---

## Response

```json
[
  {
    "volunteer_id": "uuid",         // UUID string
    "username": "string",           // fallback to first 8 chars of UUID if no username set
    "display_name": "string | null",
    "overall_score": 72.5,          // float, 0–100
    "badge_tier": "gold",           // "platinum"|"gold"|"silver"|"bronze"|"none"
    "elite_status": false,          // bool — top 10% of active volunteers
    "location": "string | null",
    "languages": ["az", "en"],      // string[]
    "similarity": 0.87              // float | null — cosine similarity from pgvector.
                                    // ⚠️ NULL when rule-based fallback is used (embedding unavailable).
                                    // Frontend MUST handle null — do not assume always populated.
  }
]
```

### similarity field — IMPORTANT
The search uses **two paths**:
1. **Semantic (pgvector):** Gemini embeddings + cosine similarity. `similarity` is populated (0.0–1.0).
2. **Rule-based fallback:** Used when Gemini embedding API is slow/unavailable. `similarity = null`.

Frontend must not crash on `similarity: null`. Suggested handling:
```typescript
const score = result.similarity != null ? `${(result.similarity * 100).toFixed(0)}% match` : null;
```

---

## Search Algorithm

1. Attempt Gemini text-embedding-004 on `query`
2. If embedding available → call `match_volunteers` RPC (pgvector cosine similarity)
   - Filters: `min_aura >= payload.min_aura`
   - Returns: top `limit + offset` by similarity, sliced to `[offset : offset + limit]`
3. If embedding unavailable → rule-based:
   - Query `aura_scores` WHERE `total_score >= min_aura`
   - Optional: filter by `badge_tier`
   - Limit + offset applied
4. Enrich with `profiles` (username, display_name, location, languages)
5. Post-filter: `languages`, `location` (applied after DB query)

---

## Error Responses

| Code | Body | When |
|------|------|------|
| 422 | `{"code": "INVALID_BADGE_TIER", ...}` | badge_tier not in allowed list |
| 401 | `{"code": "NOT_AUTHENTICATED"}` | No auth header |
| 429 | rate limit response | >60 requests/min |

---

## Notes for Sprint 4 UI

- Response is a flat array (no `{data, meta}` envelope) — access directly as array
- Empty result: `[]` — not null, not `{data: []}`
- Pagination: use `offset` + `limit`. No cursor. No total count in response.
- For org dashboard: show `similarity` only when non-null (show nothing if rule-based)
- `visible_to_orgs=TRUE` filter applied server-side — only opted-in volunteers appear
