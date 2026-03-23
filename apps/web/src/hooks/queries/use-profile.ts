"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/api/client";
import { useAuthToken } from "./use-auth-token";
import type { Profile, UpdateProfileRequest } from "@/lib/api/types";

// TODO: Replace with @hey-api/openapi-ts generated hooks after pnpm generate:api

export function useProfile() {
  const getToken = useAuthToken();

  return useQuery<Profile, ApiError>({
    queryKey: ["profile", "me"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<Profile>("/api/profiles/me", { token });
    },
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}

export function usePublicProfile(username: string | undefined) {
  const getToken = useAuthToken();

  return useQuery<Profile, ApiError>({
    queryKey: ["profile", username],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<Profile>(`/api/profiles/${username}`, { token });
    },
    enabled: !!username,
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}

export function useUpdateProfile() {
  const getToken = useAuthToken();
  const queryClient = useQueryClient();

  return useMutation<Profile, ApiError, UpdateProfileRequest>({
    mutationFn: async (data) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<Profile>("/api/profiles/me", {
        method: "PUT",
        token,
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile", "me"] });
    },
  });
}
