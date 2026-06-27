import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import posthog from "posthog-js";

/*
  Shared browser runtime for the candidate runner: anonymous Supabase session
  (pilot session mechanism — NOT the identity layer; SİMA comes later),
  authenticated API fetch, and PostHog funnel events.
*/

// Publishable values — safe in the bundle by design. Env overrides for staging.
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || "https://dwdgzfusjsobnixgyzjk.supabase.co";
const SUPABASE_KEY = process.env.NEXT_PUBLIC_SUPABASE_KEY || "sb_publishable_lVUcn3G29V449ltPzCJF4g_ID5G3Ud9";
// Browser API calls go SAME-ORIGIN to `/api`; `next.config.mjs` rewrites `/api/*`
// to NEXT_PUBLIC_API_URL (Railway) server-side. This avoids cross-origin CORS from
// the dev origin (localhost) and any non-allowlisted host. Do NOT hit Railway directly here.

let supabaseSingleton: SupabaseClient | null = null;

export function supabase(): SupabaseClient {
  if (!supabaseSingleton) {
    supabaseSingleton = createClient(SUPABASE_URL, SUPABASE_KEY);
  }
  return supabaseSingleton;
}

/** Anonymous session for the pilot. Reuses an existing session across reloads. */
export async function ensureSession(): Promise<string> {
  const sb = supabase();
  const { data } = await sb.auth.getSession();
  if (data.session) return data.session.access_token;
  const { data: anon, error } = await sb.auth.signInAnonymously();
  if (error || !anon.session) throw new Error(error?.message || "Could not start a session");
  return anon.session.access_token;
}

export async function api<T>(path: string, init?: RequestInit & { json?: unknown }): Promise<T> {
  const token = await ensureSession();
  const res = await fetch(`/api${path}`, {
    ...init,
    method: init?.json !== undefined ? init?.method || "POST" : init?.method || "GET",
    headers: {
      Authorization: `Bearer ${token}`,
      ...(init?.json !== undefined ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
    body: init?.json !== undefined ? JSON.stringify(init.json) : init?.body,
  });
  if (res.status === 204) return undefined as T;
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = (body as { detail?: { code?: string; message?: string; session_id?: string } }).detail;
    const err = new Error(detail?.message || `API ${res.status}`) as Error & {
      code?: string;
      sessionId?: string;
      status?: number;
    };
    err.code = detail?.code;
    err.sessionId = detail?.session_id;
    err.status = res.status;
    throw err;
  }
  return body as T;
}

let posthogReady = false;

export function track(event: string, props?: Record<string, unknown>): void {
  const key = process.env.NEXT_PUBLIC_POSTHOG_KEY;
  if (!key) return; // instrumentation off until the key is wired
  if (!posthogReady) {
    posthog.init(key, {
      api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://us.i.posthog.com",
      autocapture: false,
      capture_pageview: false,
    });
    posthogReady = true;
  }
  posthog.capture(event, props);
}
