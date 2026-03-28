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
