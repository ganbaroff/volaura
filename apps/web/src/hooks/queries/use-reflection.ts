"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api/client";

interface ReflectionResponse {
  reflection: string | null;
  cached: boolean;
}

export function useReflection(enabled: boolean) {
  return useQuery<string | null>({
    queryKey: ["atlas-reflection"],
    queryFn: async () => {
      const data = await apiFetch<ReflectionResponse>("/aura/me/reflection");
      return data.reflection;
    },
    enabled,
    staleTime: 24 * 60 * 60 * 1000,
    retry: 1,
  });
}
