"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { configureApiClient } from "@/lib/api/configure-client";

// SECURITY FIX (Sprint E2): Configure generated API client with auth interceptor.
// Called SYNCHRONOUSLY at module load — NOT in useEffect.
// useEffect runs AFTER first render, but React Query hooks fetch on mount (BEFORE useEffect).
// This race condition caused all /me endpoints to get 401 (no Bearer token on first requests).
// Session 85 fix: move to module scope so interceptor is ready before any component renders.
configureApiClient();

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
