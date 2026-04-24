"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listEventsApiEventsGet,
  getEventApiEventsEventIdGet,
  createEventApiEventsPost,
  registerForEventApiEventsEventIdRegisterPost,
  myRegistrationsApiEventsMyRegistrationsGet,
} from "@/lib/api/generated";
import { apiFetch, ApiError, toApiError } from "@/lib/api/client";
import { useAuthToken } from "./use-auth-token";
import type { EventResponse, EventCreate, RegistrationResponse } from "@/lib/api/types";

export function useEvents(params?: { status?: string; limit?: number; offset?: number }) {
  return useQuery<EventResponse[], ApiError>({
    queryKey: ["events", params],
    queryFn: async () => {
      const { data, error } = await listEventsApiEventsGet({
        query: {
          status: params?.status,
          limit: params?.limit,
          offset: params?.offset,
        },
      });
      if (error) throw toApiError(error, { message: "Failed to fetch events" });
      return (data ?? []) as unknown as EventResponse[];
    },
    staleTime: 2 * 60 * 1000,
    retry: 2,
  });
}

export function useEvent(eventId: string | undefined) {
  return useQuery<EventResponse, ApiError>({
    queryKey: ["events", eventId],
    queryFn: async () => {
      const { data, error } = await getEventApiEventsEventIdGet({
        path: { event_id: eventId! },
      });
      if (error) throw toApiError(error, { message: "Failed to fetch event" });
      if (!data) throw new ApiError(500, "EMPTY_RESPONSE", "Failed to fetch event");
      return data as unknown as EventResponse;
    },
    enabled: !!eventId,
    staleTime: 2 * 60 * 1000,
    retry: 2,
  });
}

export interface MyEventResponse extends EventResponse {
  registration_id?: string | null;
  registration_status?: string | null;
  registered_at?: string | null;
  checked_in_at?: string | null;
  role?: string | null;
}

export function useMyEventTimeline() {
  const getToken = useAuthToken();

  return useQuery<MyEventResponse[], ApiError>({
    queryKey: ["events", "my", "timeline"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<MyEventResponse[]>("/events/my/timeline", { token });
    },
    staleTime: 2 * 60 * 1000,
    retry: 2,
  });
}

export function useMyOwnedEvents() {
  const getToken = useAuthToken();

  return useQuery<EventResponse[], ApiError>({
    queryKey: ["events", "my", "owned"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<EventResponse[]>("/events/my/owned", { token });
    },
    staleTime: 2 * 60 * 1000,
    retry: 2,
  });
}

export function useMyRegistrations() {
  return useQuery<RegistrationResponse[], ApiError>({
    queryKey: ["events", "my", "registrations"],
    queryFn: async () => {
      const { data, error } = await myRegistrationsApiEventsMyRegistrationsGet();
      if (error) throw toApiError(error, { message: "Failed to fetch registrations" });
      return (data ?? []) as unknown as RegistrationResponse[];
    },
    staleTime: 2 * 60 * 1000,
    retry: 2,
  });
}

// Backward-compatible alias while pages migrate to explicit names.
export const useMyEvents = useMyEventTimeline;

export interface EventAttendeeRow {
  registration_id: string;
  professional_id: string;
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

/** Rate a professional as coordinator — POST /events/{id}/rate/coordinator */
export function useRateProfessional(eventId: string) {
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

  return useMutation<EventResponse, ApiError, EventCreate>({
    mutationFn: async (body) => {
      const { data, error } = await createEventApiEventsPost({ body });
      if (error) throw toApiError(error, { message: "Failed to create event" });
      if (!data) throw new ApiError(500, "EMPTY_RESPONSE", "Failed to create event");
      return data as unknown as EventResponse;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["events"] });
    },
  });
}

export function useRegisterForEvent() {
  const queryClient = useQueryClient();

  return useMutation<RegistrationResponse, ApiError, { eventId: string }>({
    mutationFn: async ({ eventId }) => {
      const { data, error } = await registerForEventApiEventsEventIdRegisterPost({
        path: { event_id: eventId },
      });
      if (error) throw toApiError(error, { message: "Failed to register for event" });
      if (!data) throw new ApiError(500, "EMPTY_RESPONSE", "Failed to register for event");
      return data as unknown as RegistrationResponse;
    },
    onSuccess: (_data, { eventId }) => {
      queryClient.invalidateQueries({ queryKey: ["events", eventId] });
    },
  });
}
