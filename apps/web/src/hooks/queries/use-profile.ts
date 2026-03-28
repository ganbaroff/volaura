"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getMyProfileApiProfilesMeGet,
  getPublicProfileApiProfilesUsernameGet,
  updateMyProfileApiProfilesMePut,
} from "@/lib/api/generated";
import type { Profile, UpdateProfileRequest } from "@/lib/api/types";
import type { ProfileResponse } from "@/lib/api/generated/types.gen";
import { toProfile } from "@/lib/api/types";
import { apiFetch, ApiError } from "@/lib/api/client";
import { useAuthToken } from "./use-auth-token";

export interface DiscoverableVolunteer {
  id: string;
  username: string;
  display_name: string | null;
  avatar_url: string | null;
  bio: string | null;
  location: string | null;
  languages: string[];
  total_score: number | null;
  badge_tier: string | null;
}

export function useProfile() {
  return useQuery<Profile>({
    queryKey: ["profile", "me"],
    queryFn: async () => {
      const { data, error } = await getMyProfileApiProfilesMeGet();
      if (error || !data) throw new Error("Failed to fetch profile");
      return toProfile(data as unknown as ProfileResponse);
    },
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}

export function usePublicProfile(username: string | undefined) {
  return useQuery<Profile>({
    queryKey: ["profile", username],
    queryFn: async () => {
      const { data, error } = await getPublicProfileApiProfilesUsernameGet({
        path: { username: username! },
      });
      if (error || !data) throw new Error("Failed to fetch profile");
      return toProfile(data as unknown as ProfileResponse);
    },
    enabled: !!username,
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}

/** Org-only: list all opted-in volunteers ordered by AURA score */
export function useDiscoverableVolunteers(params?: { limit?: number; offset?: number }) {
  const getToken = useAuthToken();

  return useQuery<DiscoverableVolunteer[], ApiError>({
    queryKey: ["profiles", "public", params],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      const search = new URLSearchParams();
      if (params?.limit) search.set("limit", String(params.limit));
      if (params?.offset) search.set("offset", String(params.offset));
      const qs = search.toString();
      return apiFetch<DiscoverableVolunteer[]>(`/api/profiles/public${qs ? `?${qs}` : ""}`, { token });
    },
    staleTime: 2 * 60 * 1000,
    retry: 1,
    throwOnError: false,
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();

  return useMutation<Profile, Error, UpdateProfileRequest>({
    mutationFn: async (body) => {
      const { data, error } = await updateMyProfileApiProfilesMePut({
        body,
      });
      if (error || !data) throw new Error("Failed to update profile");
      return toProfile(data as unknown as ProfileResponse);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile", "me"] });
    },
  });
}
