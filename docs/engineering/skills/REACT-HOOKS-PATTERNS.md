# React Hooks Patterns — Anti-Bug Reference

**Version:** 1.0 | **Created:** 2026-03-29 (Sprint A9)
**Why this exists:** Sprint A4 shipped `useAuthToken()` inside `mutationFn` callback — React rules violation. This pattern has zero runtime warning on the server but silently breaks on client. This file prevents the class.

---

## RULE 1 — Hooks NEVER Inside Callbacks

**Wrong:**
```typescript
const myMutation = useMutation({
  mutationFn: async (payload) => {
    const getToken = useAuthToken(); // ❌ HOOK INSIDE CALLBACK
    const token = await getToken();
    ...
  }
});
```

**Correct:**
```typescript
function useMyMutation() {
  const getToken = useAuthToken(); // ✅ HOOK AT TOP LEVEL
  return useMutation({
    mutationFn: async (payload) => {
      const token = await getToken(); // call the function, not the hook
      ...
    }
  });
}
```

**Why it breaks:** React hooks must be called at the top level of a component or custom hook. Every `mutationFn`, `queryFn`, `onClick`, `useEffect` callback is NOT a hook call site. The lint rule `react-hooks/rules-of-hooks` catches this statically — but only if ESLint is running.

**Verify before every mutation hook:** Grep for `use[A-Z]` inside `mutationFn: async` — if found, it's broken.

---

## RULE 2 — isMounted Guard on Async State Updates

Any component with async operations that might resolve after unmount needs an `isMounted` ref:

```typescript
export default function MyPage() {
  const isMounted = useRef(true);
  useEffect(() => () => { isMounted.current = false; }, []);

  async function handleAction() {
    const result = await someAsyncOp();
    if (!isMounted.current) return; // guard before setState
    setResult(result);
  }
}
```

**When required:** Any page with `useState` + async `fetch`/`apiFetch`/`supabase` calls where navigation can happen during the await.

**When NOT required:** TanStack Query hooks handle this internally — `useQuery`/`useMutation` won't update unmounted component state.

---

## RULE 3 — Token Must Be Fetched at Call Time, Not Stored in State

**Wrong:**
```typescript
const [token, setToken] = useState<string | null>(null);
useEffect(() => {
  getToken().then(setToken);
}, []);
// ... later: headers: { Authorization: `Bearer ${token}` }
```

**Correct:**
```typescript
const getToken = useAuthToken();
// ... in async handler:
const token = await getToken(); // always fresh
```

**Why:** Supabase JWTs expire. A stored token can be stale. `useAuthToken()` always returns a fresh or refreshed token from the Supabase session.

---

## RULE 4 — One-Shot Mutations (Disable After Submit)

For irreversible actions (rating, deletion, payment):
```typescript
const [submitted, setSubmitted] = useState(false);
// In UI:
<button disabled={submitted || mutation.isPending} onClick={() => {
  setSubmitted(true);
  mutation.mutate(payload);
}}>
```

The `submitted` flag prevents double-submit even after mutation resolves. This is separate from `mutation.isPending` which only blocks during the in-flight request.

**Applies to:** Star ratings, confirm-delete buttons, payment triggers, assessment submission.

---

## RULE 5 — Envelope Unwrapping

All API responses from Volaura backend are wrapped: `{ data: T, meta?: M }`.

```typescript
// apiFetch already unwraps if using the typed helper — check behavior:
// apiFetch<T>() → returns T (already unwrapped)

// Raw fetch (multipart uploads, special cases):
const json = await response.json();
const data: T = json.data !== undefined ? json.data : json; // handle both
```

**Why both branches:** Legacy endpoints and new endpoints differ. Some return raw, some envelope. The safe pattern handles both.

---

## Checklist — Before Committing Any Hook File

- [ ] All `useX()` calls at top level of custom hook or component, not inside callbacks
- [ ] `mutationFn` uses pre-hoisted `getToken = useAuthToken()` not inline call
- [ ] Async state updates guarded by `isMounted.current` OR component uses TanStack Query only
- [ ] Token fetched fresh at call time (not stored in useState)
- [ ] One-shot buttons use `submitted` state for irreversible actions
- [ ] API response envelope unwrapped with `json.data ?? json` fallback pattern

---

## Cross-References

- `apps/web/src/hooks/queries/use-events.ts:useRateVolunteer` — reference implementation (Sprint A4 fixed)
- `apps/web/src/app/[locale]/(dashboard)/my-organization/page.tsx` — isMounted example
- `apps/web/src/lib/api/client.ts` — apiFetch implementation (envelope unwrapping)
