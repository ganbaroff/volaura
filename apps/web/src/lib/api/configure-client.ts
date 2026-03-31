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
import { createClient as createSupabaseClient } from "@/lib/supabase/client";

let configured = false;

export function configureApiClient(): void {
  if (configured) return;
  configured = true;

  // Set the correct base URL from environment
  client.setConfig({
    baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  });

  // Inject Supabase Bearer token on every request
  client.interceptors.request.use(async (request) => {
    try {
      const supabase = createSupabaseClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (session?.access_token) {
        request.headers.set("Authorization", `Bearer ${session.access_token}`);
      }
    } catch {
      // Never block the request if auth lookup fails — let the API return 401
      // so the frontend auth state can handle it gracefully
    }
    return request;
  });
}
