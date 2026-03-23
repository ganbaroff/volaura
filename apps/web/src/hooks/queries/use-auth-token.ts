"use client";

import { useCallback } from "react";
import { createClient } from "@/lib/supabase/client";

/**
 * Returns a function that gets the current Supabase access token.
 * Used by all API query hooks to pass Bearer token to FastAPI.
 */
// TODO: Replace with @hey-api/openapi-ts auth interceptor after pnpm generate:api
export function useAuthToken() {
  return useCallback(async (): Promise<string | null> => {
    const supabase = createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();
    return session?.access_token ?? null;
  }, []);
}
