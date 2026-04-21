/**
 * INTERIM API client — manual fetch wrapper.
 * TODO: Replace with @hey-api/openapi-ts generated code after `pnpm generate:api`
 *
 * All API responses use envelope: { data: T, meta: { timestamp, request_id } }
 * Error responses: { error: { code, message, details? } }
 */

import { getFreshAccessToken } from "@/lib/api/get-fresh-token";

// Relative path — Vercel rewrites to NEXT_PUBLIC_API_URL (or localhost in dev)
// Production: volaura.app/api → modest-happiness-production.up.railway.app/api
// Dev: localhost:3000/api → localhost:8000/api
export const API_BASE = "/api";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    public readonly detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

interface FetchOptions extends Omit<RequestInit, "headers"> {
  token?: string;
  headers?: Record<string, string>;
}

/**
 * Fetch wrapper that handles auth headers and unwraps the API envelope.
 * Returns the unwrapped `.data` from `{ data, meta }` responses.
 */
// TODO: Replace with @hey-api/openapi-ts generated code after pnpm generate:api
export async function apiFetch<T>(
  path: string,
  options: FetchOptions = {},
): Promise<T> {
  const { token: explicitToken, headers: extraHeaders, ...fetchOptions } = options;

  // Auto-inject Supabase session token if none provided explicitly.
  // getFreshAccessToken() refreshes the JWT when expired or expiring within
  // 60 seconds — same logic as the generated SDK interceptor in configure-client.ts.
  let token = explicitToken;
  if (!token) {
    token = (await getFreshAccessToken()) ?? undefined;
  }

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
    ...extraHeaders,
  };

  // Normalize: strip leading /api if caller already includes it (prevents /api/api/... double prefix)
  const normalizedPath = path.startsWith("/api/") ? path.slice(4) : path;
  const response = await fetch(`${API_BASE}${normalizedPath}`, {
    ...fetchOptions,
    headers,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({
      error: { code: "UNKNOWN", message: response.statusText },
    }));
    const err = body.error ?? body.detail ?? { code: "UNKNOWN", message: response.statusText };
    throw new ApiError(
      response.status,
      err.code ?? "UNKNOWN",
      err.message ?? response.statusText,
    );
  }

  const json = await response.json();

  // Unwrap API envelope: { data: T, meta: {...} }
  // Some endpoints return raw data (e.g., health check) — handle both
  return (json.data !== undefined ? json.data : json) as T;
}
