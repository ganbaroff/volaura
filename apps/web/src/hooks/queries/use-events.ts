"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listEventsApiEventsGet,
  getEventApiEventsEventIdGet,
  createEventApiEventsPost,
  registerForEventApiEventsEventIdRegisterPost,
  myRegistrationsApiEventsMyRegistrationsGet,
} from "@/lib/api/generated";
import { apiFetch, ApiError } from "@/lib/api/client";
import { useAuthToken } from "./use-auth-token";
import type { EventResponse, EventCreate, RegistrationResponse } from "@/lib/api/types";

export function useEvents(params?: { status?: string; limit?: number; offset?: number }) {
  return useQuery<EventResponse[]>({
    queryKey: ["events", params],
    queryFn: async () => {
      const { data, error } = await listEventsApiEventsGet({
        query: {
          status: params?.status,
          limit: params?.limit,
          offset: params?.offset,
        },
      });
      if (error) throw new Error("Failed to fetch events");
      return (data ?? []) as unknown as EventResponse[];
    },
    staleTime: 2 * 60 * 1000,
    retry: 2,
  });
}

export function useEvent(eventId: string | undefined) {
  return useQuery<EventResponse>({
    queryKey: ["events", eventId],
    queryFn: async () => {
      const { data, error } = await getEventApiEventsEventIdGet({
        path: { event_id: eventId! },
      });
      if (error || !data) throw new Error("Failed to fetch event");
      return data as unknown as EventResponse;
    },
    enabled: !!eventId,
    staleTime: 2 * 60 * 1000,
    retry: 2,
  });
}

// /api/events/my returns EventResponse[] with registration context — not in generated SDK
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

export interface EventAttendeeRow {
  registration_id: string;
  volunteer_id: string;
  status: string;
  registered_at: string;
  checked_in_at: string | null;
  display_name: string | null;
  username: string | null;
  total_score: number | null;
  badge_tier: string | null;
}

export interface CoordinatorRatingPayload {
  registration_id: string;
  rating: number;
  feedback?: string;
}

/** Rate a volunteer as coordinator — POST /events/{id}/rate/coordinator */
export function useRateVolunteer(eventId: string) {
  const getToken = useAuthToken();
  const queryClient = useQueryClient();

  return useMutation<unknown, ApiError, CoordinatorRatingPayload>({
    mutationFn: async (payload) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch(`/api/events/${eventId}/rate/coordinator`, {
        method: "POST",
        token,
        body: JSON.stringify(payload),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["events", eventId, "attendees"] });
    },
  });
}

/** Enriched attendee list — org owner only */
export function useEventAttendees(eventId: string | undefined) {
  const getToken = useAuthToken();

  return useQuery<EventAttendeeRow[], ApiError>({
    queryKey: ["events", eventId, "attendees"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<EventAttendeeRow[]>(`/api/events/${eventId}/attendees`, { token });
    },
    enabled: !!eventId,
    staleTime: 60 * 1000,
    retry: 1,
    throwOnError: false,
  });
}

export function useCreateEvent() {
  const queryClient = useQueryClient();

  return useMutation<EventResponse, Error, EventCreate>({
    mutationFn: async (body) => {
      const { data, error } = await createEventApiEventsPost({ body });
      if (error || !data) throw new Error("Failed to create event");
      return data as unknown as EventResponse;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["events"] });
    },
  });
}

export function useRegisterForEvent() {
  const queryClient = useQueryClient();

  return useMutation<RegistrationResponse, Error, { eventId: string }>({
    mutationFn: async ({ eventId }) => {
      const { data, error } = await registerForEventApiEventsEventIdRegisterPost({
        path: { event_id: eventId },
      });
      if (error || !data) throw new Error("Failed to register for event");
      return data as unknown as RegistrationResponse;
    },
    onSuccess: (_data, { eventId }) => {
      queryClient.invalidateQueries({ queryKey: ["events", eventId] });
    },
  });
}
