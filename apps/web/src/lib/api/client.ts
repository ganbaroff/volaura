/**
 * INTERIM API client — manual fetch wrapper.
 * TODO: Replace with @hey-api/openapi-ts generated code after `pnpm generate:api`
 *
 * All API responses use envelope: { data: T, meta: { timestamp, request_id } }
 * Error responses: { error: { code, message, details? } }
 */

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
  const { token, headers: extraHeaders, ...fetchOptions } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
    ...extraHeaders,
  };

  const response = await fetch(`${API_BASE}${path}`, {
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
