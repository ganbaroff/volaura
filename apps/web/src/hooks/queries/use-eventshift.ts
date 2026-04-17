"use client";

/**
 * EventShift hooks — MVP. Uses hand-rolled apiFetch since the generated SDK
 * has not yet been regenerated against the new /api/eventshift/* router.
 * Regenerate via `pnpm generate:api` once the router is deployed.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError, apiFetch } from "@/lib/api/client";

import { useAuthToken } from "./use-auth-token";

// ── Types ───────────────────────────────────────────────────────────────────

export type EventShiftStatus = "planning" | "staffing" | "live" | "closed" | "cancelled";
export type UnitStatus = "open" | "staffed" | "live" | "closed";
export type AssignmentRole = "lead" | "staff" | "backup" | "volunteer";
export type AssignmentStatus =
  | "assigned"
  | "accepted"
  | "declined"
  | "checked_in"
  | "completed"
  | "no_show";
export type MetricType =
  | "attendance"
  | "handover_integrity"
  | "incident"
  | "incident_closure"
  | "reliability_proof";

export interface EventShiftEvent {
  id: string;
  org_id: string;
  slug: string;
  name: string;
  description: string | null;
  start_at: string;
  end_at: string;
  timezone: string;
  location: Record<string, unknown> | null;
  status: EventShiftStatus;
  created_at: string;
  updated_at: string;
}

export interface EventShiftDepartment {
  id: string;
  org_id: string;
  event_id: string;
  name: string;
  description: string | null;
  color_hex: string | null;
  lead_user_id: string | null;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface EventShiftArea {
  id: string;
  org_id: string;
  department_id: string;
  name: string;
  description: string | null;
  location: Record<string, unknown> | null;
  coordinator_user_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface EventShiftUnit {
  id: string;
  org_id: string;
  area_id: string;
  name: string;
  description: string | null;
  shift_start: string;
  shift_end: string;
  required_headcount: number;
  required_skills: string[];
  status: UnitStatus;
  created_at: string;
  updated_at: string;
}

export interface EventShiftAssignment {
  id: string;
  org_id: string;
  unit_id: string;
  user_id: string;
  role: AssignmentRole;
  status: AssignmentStatus;
  notes: string | null;
  assigned_at: string;
  updated_at: string;
}

export interface EventShiftMetric {
  id: string;
  org_id: string;
  unit_id: string;
  metric_type: MetricType;
  value: number | null;
  payload: Record<string, unknown> | null;
  recorded_at: string;
  recorded_by: string | null;
  created_at: string;
}

// ── Create payloads ─────────────────────────────────────────────────────────

export interface EventShiftEventCreate {
  slug: string;
  name: string;
  description?: string;
  start_at: string;
  end_at: string;
  timezone?: string;
  location?: Record<string, unknown>;
  status?: EventShiftStatus;
}

export interface DepartmentCreate {
  name: string;
  description?: string;
  color_hex?: string;
  lead_user_id?: string;
  sort_order?: number;
}

export interface AreaCreate {
  name: string;
  description?: string;
  location?: Record<string, unknown>;
  coordinator_user_id?: string;
}

export interface UnitCreatePayload {
  name: string;
  description?: string;
  shift_start: string;
  shift_end: string;
  required_headcount?: number;
  required_skills?: string[];
  status?: UnitStatus;
}

export interface AssignmentCreate {
  user_id: string;
  role?: AssignmentRole;
  notes?: string;
}

export interface MetricCreate {
  metric_type: MetricType;
  value?: number;
  payload?: Record<string, unknown>;
  recorded_at?: string;
}

// ── Activation gate diagnostic ──────────────────────────────────────────────

export interface ActivationState {
  org_id: string;
  module_slug: string;
  active: boolean;
}

export function useEventShiftActivation() {
  const getToken = useAuthToken();
  return useQuery<ActivationState, ApiError>({
    queryKey: ["eventshift", "activation"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<ActivationState>("/eventshift/debug/activation-state", { token });
    },
    staleTime: 30_000,
    retry: 0,
  });
}

// ── Events ──────────────────────────────────────────────────────────────────

export function useEventShiftEvents(status?: EventShiftStatus) {
  const getToken = useAuthToken();
  return useQuery<EventShiftEvent[], ApiError>({
    queryKey: ["eventshift", "events", status ?? "all"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      const q = status ? `?status=${status}` : "";
      return apiFetch<EventShiftEvent[]>(`/eventshift/events${q}`, { token });
    },
    staleTime: 60_000,
  });
}

export function useEventShiftEvent(eventId: string | undefined) {
  const getToken = useAuthToken();
  return useQuery<EventShiftEvent, ApiError>({
    queryKey: ["eventshift", "events", eventId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<EventShiftEvent>(`/eventshift/events/${eventId}`, { token });
    },
    enabled: !!eventId,
    staleTime: 30_000,
  });
}

export function useCreateEventShiftEvent() {
  const getToken = useAuthToken();
  const qc = useQueryClient();
  return useMutation<EventShiftEvent, ApiError, EventShiftEventCreate>({
    mutationFn: async (payload) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<EventShiftEvent>("/eventshift/events", {
        method: "POST",
        token,
        body: JSON.stringify(payload),
        headers: { "Content-Type": "application/json" },
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["eventshift", "events"] });
    },
  });
}

// ── Departments ─────────────────────────────────────────────────────────────

export function useDepartments(eventId: string | undefined) {
  const getToken = useAuthToken();
  return useQuery<EventShiftDepartment[], ApiError>({
    queryKey: ["eventshift", "departments", eventId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<EventShiftDepartment[]>(
        `/eventshift/events/${eventId}/departments`,
        { token },
      );
    },
    enabled: !!eventId,
    staleTime: 30_000,
  });
}

export function useCreateDepartment(eventId: string) {
  const getToken = useAuthToken();
  const qc = useQueryClient();
  return useMutation<EventShiftDepartment, ApiError, DepartmentCreate>({
    mutationFn: async (payload) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<EventShiftDepartment>(
        `/eventshift/events/${eventId}/departments`,
        {
          method: "POST",
          token,
          body: JSON.stringify(payload),
          headers: { "Content-Type": "application/json" },
        },
      );
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["eventshift", "departments", eventId] });
    },
  });
}

// ── Areas ───────────────────────────────────────────────────────────────────

export function useAreas(departmentId: string | undefined) {
  const getToken = useAuthToken();
  return useQuery<EventShiftArea[], ApiError>({
    queryKey: ["eventshift", "areas", departmentId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<EventShiftArea[]>(
        `/eventshift/departments/${departmentId}/areas`,
        { token },
      );
    },
    enabled: !!departmentId,
    staleTime: 30_000,
  });
}

export function useCreateArea(departmentId: string) {
  const getToken = useAuthToken();
  const qc = useQueryClient();
  return useMutation<EventShiftArea, ApiError, AreaCreate>({
    mutationFn: async (payload) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<EventShiftArea>(
        `/eventshift/departments/${departmentId}/areas`,
        {
          method: "POST",
          token,
          body: JSON.stringify(payload),
          headers: { "Content-Type": "application/json" },
        },
      );
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["eventshift", "areas", departmentId] });
    },
  });
}

// ── Units ───────────────────────────────────────────────────────────────────

export function useUnits(areaId: string | undefined) {
  const getToken = useAuthToken();
  return useQuery<EventShiftUnit[], ApiError>({
    queryKey: ["eventshift", "units", areaId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<EventShiftUnit[]>(`/eventshift/areas/${areaId}/units`, {
        token,
      });
    },
    enabled: !!areaId,
    staleTime: 30_000,
  });
}

export function useCreateUnit(areaId: string) {
  const getToken = useAuthToken();
  const qc = useQueryClient();
  return useMutation<EventShiftUnit, ApiError, UnitCreatePayload>({
    mutationFn: async (payload) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<EventShiftUnit>(`/eventshift/areas/${areaId}/units`, {
        method: "POST",
        token,
        body: JSON.stringify(payload),
        headers: { "Content-Type": "application/json" },
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["eventshift", "units", areaId] });
    },
  });
}

// ── Assignments ─────────────────────────────────────────────────────────────

export function useAssignments(unitId: string | undefined) {
  const getToken = useAuthToken();
  return useQuery<EventShiftAssignment[], ApiError>({
    queryKey: ["eventshift", "assignments", unitId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<EventShiftAssignment[]>(
        `/eventshift/units/${unitId}/assignments`,
        { token },
      );
    },
    enabled: !!unitId,
    staleTime: 30_000,
  });
}

export function useCreateAssignment(unitId: string) {
  const getToken = useAuthToken();
  const qc = useQueryClient();
  return useMutation<EventShiftAssignment, ApiError, AssignmentCreate>({
    mutationFn: async (payload) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<EventShiftAssignment>(
        `/eventshift/units/${unitId}/assignments`,
        {
          method: "POST",
          token,
          body: JSON.stringify(payload),
          headers: { "Content-Type": "application/json" },
        },
      );
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["eventshift", "assignments", unitId] });
    },
  });
}

// ── Metrics ─────────────────────────────────────────────────────────────────

export function useMetrics(
  unitId: string | undefined,
  metric_type?: MetricType,
) {
  const getToken = useAuthToken();
  return useQuery<EventShiftMetric[], ApiError>({
    queryKey: ["eventshift", "metrics", unitId, metric_type ?? "all"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      const q = metric_type ? `?metric_type=${metric_type}` : "";
      return apiFetch<EventShiftMetric[]>(
        `/eventshift/units/${unitId}/metrics${q}`,
        { token },
      );
    },
    enabled: !!unitId,
    staleTime: 30_000,
  });
}

export function useRecordMetric(unitId: string) {
  const getToken = useAuthToken();
  const qc = useQueryClient();
  return useMutation<EventShiftMetric, ApiError, MetricCreate>({
    mutationFn: async (payload) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<EventShiftMetric>(
        `/eventshift/units/${unitId}/metrics`,
        {
          method: "POST",
          token,
          body: JSON.stringify(payload),
          headers: { "Content-Type": "application/json" },
        },
      );
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["eventshift", "metrics", unitId] });
    },
  });
}
