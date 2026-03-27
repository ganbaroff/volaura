"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/api/client";
import { useAuthToken } from "./use-auth-token";

// ── Types (mirrors Pydantic schemas in apps/api/app/schemas/brandedby.py) ──

export interface AITwin {
  id: string;
  user_id: string;
  display_name: string;
  tagline: string | null;
  photo_url: string | null;
  voice_id: string | null;
  personality_prompt: string | null;
  status: "draft" | "active" | "suspended";
  created_at: string;
  updated_at: string;
}

export interface Generation {
  id: string;
  twin_id: string;
  user_id: string;
  gen_type: "video" | "audio" | "text_chat";
  input_text: string;
  output_url: string | null;
  thumbnail_url: string | null;
  status: "queued" | "processing" | "completed" | "failed";
  error_message: string | null;
  queue_position: number | null;
  crystal_cost: number;
  duration_seconds: number | null;
  processing_started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

// ── Queries ────────────────────────────────────────────────────────────────

export function useMyTwin() {
  const getToken = useAuthToken();

  return useQuery<AITwin | null, ApiError>({
    queryKey: ["brandedby", "twin"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<AITwin | null>("/api/brandedby/twins", { token });
    },
    staleTime: 2 * 60 * 1000,
    retry: 1,
  });
}

export function useGenerations(limit = 20) {
  const getToken = useAuthToken();

  return useQuery<Generation[], ApiError>({
    queryKey: ["brandedby", "generations"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<Generation[]>(`/api/brandedby/generations?limit=${limit}`, { token });
    },
    staleTime: 30 * 1000,
    retry: 1,
  });
}

export function useGeneration(genId: string | undefined) {
  const getToken = useAuthToken();

  return useQuery<Generation, ApiError>({
    queryKey: ["brandedby", "generation", genId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<Generation>(`/api/brandedby/generations/${genId}`, { token });
    },
    enabled: !!genId,
    staleTime: 10 * 1000,
    // Poll every 5s while processing/queued
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "queued" || status === "processing" ? 5000 : false;
    },
    retry: 1,
  });
}

// ── Mutations ─────────────────────────────────────────────────────────────

interface CreateTwinInput {
  display_name: string;
  tagline?: string;
  photo_url?: string;
}

export function useCreateTwin() {
  const getToken = useAuthToken();
  const queryClient = useQueryClient();

  return useMutation<AITwin, ApiError, CreateTwinInput>({
    mutationFn: async (body) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<AITwin>("/api/brandedby/twins", {
        method: "POST",
        body: JSON.stringify(body),
        token,
      });
    },
    onSuccess: (twin) => {
      queryClient.setQueryData(["brandedby", "twin"], twin);
    },
  });
}

interface UpdateTwinInput {
  twinId: string;
  data: Partial<Pick<AITwin, "display_name" | "tagline" | "photo_url">>;
}

export function useUpdateTwin() {
  const getToken = useAuthToken();
  const queryClient = useQueryClient();

  return useMutation<AITwin, ApiError, UpdateTwinInput>({
    mutationFn: async ({ twinId, data }) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<AITwin>(`/api/brandedby/twins/${twinId}`, {
        method: "PATCH",
        body: JSON.stringify(data),
        token,
      });
    },
    onSuccess: (twin) => {
      queryClient.setQueryData(["brandedby", "twin"], twin);
    },
  });
}

export function useRefreshPersonality() {
  const getToken = useAuthToken();
  const queryClient = useQueryClient();

  return useMutation<AITwin, ApiError, string>({
    mutationFn: async (twinId) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<AITwin>(`/api/brandedby/twins/${twinId}/refresh-personality`, {
        method: "POST",
        token,
      });
    },
    onSuccess: (twin) => {
      queryClient.setQueryData(["brandedby", "twin"], twin);
    },
  });
}

export function useActivateTwin() {
  const getToken = useAuthToken();
  const queryClient = useQueryClient();

  return useMutation<AITwin, ApiError, string>({
    mutationFn: async (twinId) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<AITwin>(`/api/brandedby/twins/${twinId}/activate`, {
        method: "POST",
        token,
      });
    },
    onSuccess: (twin) => {
      queryClient.setQueryData(["brandedby", "twin"], twin);
    },
  });
}

interface CreateGenerationInput {
  twin_id: string;
  gen_type?: "video" | "audio" | "text_chat";
  input_text: string;
  skip_queue?: boolean;
}

export function useCreateGeneration() {
  const getToken = useAuthToken();
  const queryClient = useQueryClient();

  return useMutation<Generation, ApiError, CreateGenerationInput>({
    mutationFn: async (body) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<Generation>("/api/brandedby/generations", {
        method: "POST",
        body: JSON.stringify(body),
        token,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["brandedby", "generations"] });
    },
  });
}
