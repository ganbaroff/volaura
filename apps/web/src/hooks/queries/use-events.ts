"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/api/client";
import { useAuthToken } from "./use-auth-token";
import type { EventResponse, EventCreate, RegistrationResponse } from "@/lib/api/types";

// TODO: Replace with @hey-api/openapi-ts generated hooks after pnpm generate:api

export function useEvents(params?: { status?: string; limit?: number; offset?: number }) {
  return useQuery<EventResponse[], ApiError>({
    queryKey: ["events", params],
    queryFn: async () => {
      const search = new URLSearchParams();
      if (params?.status) search.set("status", params.status);
      if (params?.limit) search.set("limit", String(params.limit));
      if (params?.offset) search.set("offset", String(params.offset));
      const qs = search.toString();
      return apiFetch<EventResponse[]>(`/api/events${qs ? `?${qs}` : ""}`);
    },
    staleTime: 2 * 60 * 1000,
    retry: 2,
  });
}

export function useEvent(eventId: string | undefined) {
  return useQuery<EventResponse, ApiError>({
    queryKey: ["events", eventId],
    queryFn: async () => apiFetch<EventResponse>(`/api/events/${eventId}`),
    enabled: !!eventId,
    staleTime: 2 * 60 * 1000,
    retry: 2,
  });
}

export function useMyEvents() {
  const getToken = useAuthToken();

  return useQuery<EventResponse[], ApiError>({
    queryKey: ["events", "my"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<EventResponse[]>("/api/events/my", { token });
    },
    staleTime: 2 * 60 * 1000,
    retry: 2,
  });
}

export function useCreateEvent() {
  const getToken = useAuthToken();
  const queryClient = useQueryClient();

  return useMutation<EventResponse, ApiError, EventCreate>({
    mutationFn: async (data) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<EventResponse>("/api/events", {
        method: "POST",
        token,
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["events"] });
    },
  });
}

export function useRegisterForEvent() {
  const getToken = useAuthToken();
  const queryClient = useQueryClient();

  return useMutation<RegistrationResponse, ApiError, { eventId: string }>({
    mutationFn: async ({ eventId }) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<RegistrationResponse>(`/api/events/${eventId}/register`, {
        method: "POST",
        token,
        body: JSON.stringify({}),
      });
    },
    onSuccess: (_data, { eventId }) => {
      queryClient.invalidateQueries({ queryKey: ["events", eventId] });
    },
  });
}
