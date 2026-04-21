/**
 * Onboarding draft storage — Task 4 (UX-LOGIC-AUDIT-2026-04-18 #4).
 *
 * Purpose: when POST /profiles/me fails with 401 (Supabase refresh-token
 * ladder silently died mid-session), onboarding/page.tsx bounces to
 * /login?next=<onboarding>. Without this module the user loses everything
 * they typed — name, username, location, languages, competency choice —
 * and has to re-complete three steps after logging back in.
 *
 * We persist the in-flight form state to sessionStorage (tab-scoped,
 * evicted on tab close) with a 1-hour TTL. On onboarding mount we rehydrate
 * if a valid draft exists and skip the user_metadata prefill so the draft
 * always wins.
 *
 * Schema is versioned (v=1) so future breaking changes to FormData don't
 * silently crash old drafts — drafts with a different version are dropped.
 *
 * Exported as a separate module so it can be unit-tested without mounting
 * the full onboarding React tree.
 */

export type OnboardingStep = 1 | 2 | 3;
export type OnboardingAccountType = "professional" | "organization";

export interface OnboardingFormData {
  display_name: string;
  username: string;
  location: string;
  languages: string[];
  selectedCompetency: string;
  visible_to_orgs: boolean;
}

export interface OnboardingDraft {
  v: 1;
  step: OnboardingStep;
  accountType: OnboardingAccountType;
  formData: OnboardingFormData;
  savedAt: number;
}

export const ONBOARDING_DRAFT_KEY = "onboarding:draft:v1";
export const ONBOARDING_DRAFT_TTL_MS = 60 * 60 * 1000; // 1 hour

/** Narrowly-typed guard to avoid trusting anything that arrives from storage. */
function isValidDraft(value: unknown): value is OnboardingDraft {
  if (!value || typeof value !== "object") return false;
  const d = value as Record<string, unknown>;
  if (d.v !== 1) return false;
  if (d.step !== 1 && d.step !== 2 && d.step !== 3) return false;
  if (d.accountType !== "professional" && d.accountType !== "organization") return false;
  if (typeof d.savedAt !== "number") return false;
  const f = d.formData as Record<string, unknown> | undefined;
  if (!f || typeof f !== "object") return false;
  if (typeof f.display_name !== "string") return false;
  if (typeof f.username !== "string") return false;
  if (typeof f.location !== "string") return false;
  if (!Array.isArray(f.languages)) return false;
  if (typeof f.selectedCompetency !== "string") return false;
  if (typeof f.visible_to_orgs !== "boolean") return false;
  return true;
}

/**
 * Read + validate + expire-check the draft. Returns null when:
 *  - we're on the server (no window)
 *  - sessionStorage is unavailable or throws
 *  - no draft exists
 *  - the JSON is corrupt / fails shape validation
 *  - the draft is older than ONBOARDING_DRAFT_TTL_MS (the read side evicts it too)
 */
export function readOnboardingDraft(): OnboardingDraft | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.sessionStorage.getItem(ONBOARDING_DRAFT_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as unknown;
    if (!isValidDraft(parsed)) return null;
    if (Date.now() - parsed.savedAt > ONBOARDING_DRAFT_TTL_MS) {
      // Stale — drop and report miss.
      try { window.sessionStorage.removeItem(ONBOARDING_DRAFT_KEY); } catch { /* ignore */ }
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

/**
 * Persist the in-flight onboarding state to sessionStorage. Called from the
 * 401 recovery branch before router.replace('/login'). Quota / disabled
 * storage failures are intentionally swallowed — losing the draft is
 * recoverable; throwing inside the recovery branch is not.
 */
export function writeOnboardingDraft(partial: {
  step: OnboardingStep;
  accountType: OnboardingAccountType;
  formData: OnboardingFormData;
}): void {
  if (typeof window === "undefined") return;
  try {
    const draft: OnboardingDraft = {
      v: 1,
      step: partial.step,
      accountType: partial.accountType,
      formData: partial.formData,
      savedAt: Date.now(),
    };
    window.sessionStorage.setItem(ONBOARDING_DRAFT_KEY, JSON.stringify(draft));
  } catch {
    /* ignore quota / disabled storage */
  }
}

/** Clear the draft. Called on successful handleFinish() submit. */
export function clearOnboardingDraft(): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.removeItem(ONBOARDING_DRAFT_KEY);
  } catch {
    /* ignore */
  }
}
