"use client";

/**
 * API Client Auth Interceptor
 *
 * Configures the @hey-api/client-fetch generated client to inject the
 * Supabase Bearer token on every request.
 *
 * SECURITY FIX (Sprint E2, 2026-03-30):
 * The auto-generated client.gen.ts only sets baseUrl — it has no auth headers.
 * Without this interceptor, every SDK call goes to the API without a Bearer token,
 * resulting in 401s for all authenticated endpoints.
 *
 * Usage: import and call configureApiClient() once at app startup (root layout).
 * Subsequent calls are no-ops (guarded by `configured` flag).
 *
 * Why not modify client.gen.ts directly:
 * - It's auto-generated and gets overwritten by `pnpm generate:api`
 * - This file is the correct extension point for auth configuration
 */

import { client } from "@/lib/api/generated/client.gen";
import { getFreshAccessToken } from "@/lib/api/get-fresh-token";

let configured = false;

export function configureApiClient(): void {
  if (configured) return;
  configured = true;

  // Generated client paths include /api/ prefix (e.g., /api/profiles/me).
  // baseUrl="" → browser calls volaura.app/api/... → Vercel rewrite → Railway.
  // Same-origin = no CORS. Simple.
  client.setConfig({
    baseUrl: "",
  });

  // Inject Supabase Bearer token on every request.
  // getFreshAccessToken() refreshes the JWT when expired or expiring within
  // 60 seconds, so stale tokens never reach the API silently.
  client.interceptors.request.use(async (request) => {
    try {
      const token = await getFreshAccessToken();
      if (token) {
        request.headers.set("Authorization", `Bearer ${token}`);
      }
    } catch {
      // Never block the request if token lookup fails — let the API return 401
      // so the frontend auth state can handle it gracefully.
    }
    return request;
  });
}
