/**
 * getFreshAccessToken — single source of truth for all authenticated API calls.
 *
 * Reads the current Supabase session. If the access_token is expired or will
 * expire within REFRESH_BUFFER_SECONDS, calls refreshSession() to get a new one.
 * Returns the fresh token, or null if no session exists.
 *
 * On refresh failure the stale token is returned (not null) so the downstream
 * API call proceeds and returns 401 — callers' 401 recovery paths catch that
 * cleanly. This avoids a hard fail on transient network errors during refresh.
 *
 * Consumers:
 *   lib/api/configure-client.ts — generated SDK interceptor (all @hey-api calls)
 *   lib/api/client.ts           — manual apiFetch wrapper
 *   hooks/queries/use-auth-token.ts — ~70 call sites across 13 hook files
 */

import { createClient } from "@/lib/supabase/client";

/** Refresh if the token expires within 60 seconds. */
const REFRESH_BUFFER_SECONDS = 60;

/**
 * Decode `exp` claim from a JWT without verifying the signature.
 * Returns null if the token is malformed or has no numeric `exp`.
 */
function getJwtExp(token: string): number | null {
  try {
    const parts = token.split(".");
    if (parts.length < 2) return null;
    // base64url → standard base64 (pad to multiple-of-4 length)
    const raw = parts[1];
    const padding = "=".repeat((4 - (raw.length % 4)) % 4);
    const b64 = (raw + padding).replace(/-/g, "+").replace(/_/g, "/");
    const decoded = JSON.parse(atob(b64)) as Record<string, unknown>;
    const exp = decoded.exp;
    return typeof exp === "number" ? exp : null;
  } catch {
    return null;
  }
}

/** Returns true if the token is already expired or expiring within the buffer. */
function isStale(token: string): boolean {
  const exp = getJwtExp(token);
  if (exp === null) return true; // malformed — treat as expired
  return exp < Math.floor(Date.now() / 1000) + REFRESH_BUFFER_SECONDS;
}

/**
 * Returns a valid (non-expired) Supabase access token, refreshing if needed.
 * Server-safe: returns null when called outside a browser context.
 */
export async function getFreshAccessToken(): Promise<string | null> {
  if (typeof window === "undefined") return null;
  try {
    const supabase = createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.access_token) return null;

    if (!isStale(session.access_token)) {
      // Token is fresh — no network call needed.
      return session.access_token;
    }

    // Token is expired or expiring soon — refresh it.
    const { data: refreshed, error: refreshErr } = await supabase.auth.refreshSession();
    if (refreshErr || !refreshed.session?.access_token) {
      // Refresh failed — return the stale token and let the API return 401.
      // The caller's 401 recovery path (e.g. draft-save + redirect) handles it.
      return session.access_token;
    }
    return refreshed.session.access_token;
  } catch {
    return null;
  }
}
