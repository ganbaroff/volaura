"use client";

import { useCallback } from "react";
import { getFreshAccessToken } from "@/lib/api/get-fresh-token";

/**
 * Returns a function that gets a fresh (non-expired) Supabase access token.
 * Used by all manual apiFetch query hooks to pass Bearer token to FastAPI.
 *
 * Delegates to getFreshAccessToken() — the single source of truth for token
 * refresh logic. Expired tokens are silently refreshed before returning,
 * so callers never need to handle 401-from-stale-token themselves.
 */
export function useAuthToken() {
  return useCallback(async (): Promise<string | null> => {
    return getFreshAccessToken();
  }, []);
}
