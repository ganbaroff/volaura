"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import { configureApiClient } from "@/lib/api/configure-client";

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

  // SECURITY FIX (Sprint E2): Configure generated API client with auth interceptor.
  // Called once at app startup — subsequent calls are no-ops (guarded in configure-client.ts).
  useEffect(() => {
    configureApiClient();
  }, []);

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
