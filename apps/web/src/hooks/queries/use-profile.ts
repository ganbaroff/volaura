"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/api/client";
import { useAuthToken } from "./use-auth-token";
import type { Profile, UpdateProfileRequest } from "@/lib/api/types";
import type { ProfileResponse } from "@/lib/api/generated/types.gen";
import { toProfile } from "@/lib/api/types";

export function useProfile() {
  const getToken = useAuthToken();

  return useQuery<Profile, ApiError>({
    queryKey: ["profile", "me"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      const raw = await apiFetch<ProfileResponse>("/api/profiles/me", { token });
      return toProfile(raw);
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
