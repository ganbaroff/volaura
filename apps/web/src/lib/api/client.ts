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

type UnknownRecord = Record<string, unknown>;

function asRecord(value: unknown): UnknownRecord | null {
  return typeof value === "object" && value !== null ? (value as UnknownRecord) : null;
}

function asString(value: unknown): string | undefined {
  return typeof value === "string" && value.length > 0 ? value : undefined;
}

function asNumber(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

/**
 * Normalize generated SDK / fetch errors into the same ApiError contract used
 * by the manual apiFetch layer. This preserves HTTP semantics in query hooks
 * instead of collapsing everything to plain Error("Failed to fetch ...").
 */
export function toApiError(
  error: unknown,
  fallback: {
    status?: number;
    code?: string;
    message: string;
  },
): ApiError {
  if (error instanceof ApiError) {
    return error;
  }

  const root = asRecord(error);
  const detail = asRecord(root?.detail);
  const nestedError = asRecord(root?.error);
  const response = asRecord(root?.response);
  const responseData = asRecord(response?.data);
  const responseDetail = asRecord(responseData?.detail);

  const status =
    asNumber(root?.status) ??
    asNumber(response?.status) ??
    fallback.status ??
    500;

  const code =
    asString(root?.code) ??
    asString(detail?.code) ??
    asString(nestedError?.code) ??
    asString(responseDetail?.code) ??
    fallback.code ??
    "UNKNOWN";

  const message =
    asString(detail?.message) ??
    asString(nestedError?.message) ??
    asString(responseDetail?.message) ??
    asString(root?.message) ??
    asString(response?.statusText) ??
    fallback.message;

  return new ApiError(status, code, message);
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
