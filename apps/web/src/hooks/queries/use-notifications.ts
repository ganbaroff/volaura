"use client";

import { useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuthToken } from "./use-auth-token";
import { apiFetch, ApiError } from "@/lib/api/client";
import { createClient } from "@/lib/supabase/client";

export interface NotificationItem {
  id: string;
  type: string;
  title: string;
  body: string | null;
  is_read: boolean;
  reference_id: string | null;
  created_at: string;
}

export interface NotificationList {
  notifications: NotificationItem[];
  unread_count: number;
  total: number;
}

export interface UnreadCount {
  unread_count: number;
}

const QK = {
  list: (params?: object) => ["notifications", "list", params],
  unread: () => ["notifications", "unread"],
} as const;

/** Unread count — used for sidebar badge. Polls every 2 min as baseline.
 *
 * Sprint C DSP winner: Supabase Realtime subscription fires alongside the poll
 * so the count badge updates instantly when a new notification arrives (e.g.
 * assessment complete, badge earned, profile viewed by org).
 *
 * Architecture: useRealtimeNotifications() subscribes to INSERT on the
 * notifications table for the current user. On INSERT → invalidate both
 * unread count and list queries → React re-renders within ~200ms.
 *
 * Full WebSocket / ANUS deferred until 2026-07-01 (DSP decision 2026-04-01).
 * See docs/DECISIONS.md Sprint C entry.
 */
export function useUnreadCount() {
  const getToken = useAuthToken();

  return useQuery<UnreadCount, ApiError>({
    queryKey: QK.unread(),
    queryFn: async () => {
      const token = await getToken();
      if (!token) return { unread_count: 0 };
      return apiFetch<UnreadCount>("/api/notifications/unread-count", { token });
    },
    staleTime: 2 * 60 * 1000,
    refetchInterval: 2 * 60 * 1000,
    retry: 1,
    throwOnError: false,
  });
}

/**
 * Supabase Realtime subscription — invalidates notification queries on INSERT.
 *
 * Usage: call this once near the root of the authenticated layout so the
 * subscription persists across page navigation.
 *
 *   // in apps/web/src/app/[locale]/(dashboard)/layout.tsx
 *   useRealtimeNotifications(userId);
 *
 * The subscription:
 *   - Listens to INSERT on `notifications` WHERE user_id = currentUserId
 *   - On INSERT: invalidates ["notifications", "unread"] and ["notifications", "list"]
 *   - Falls back silently if Supabase Realtime is unavailable (no user-facing error)
 *   - Cleans up channel on unmount (prevents subscription leak across auth sessions)
 *
 * RLS on `notifications` table ensures users only receive their own rows.
 * The Realtime filter `user_id=eq.{userId}` is a belt-and-suspenders
 * client-side guard on top of RLS.
 */
export function useRealtimeNotifications(userId: string | null) {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!userId) return;

    const supabase = createClient();
    const channel = supabase
      .channel(`notifications:user:${userId}`)
      .on(
        "postgres_changes",
        {
          event: "INSERT",
          schema: "public",
          table: "notifications",
          filter: `user_id=eq.${userId}`,
        },
        () => {
          // New notification arrived — refresh count badge and list immediately
          queryClient.invalidateQueries({ queryKey: QK.unread() });
          queryClient.invalidateQueries({ queryKey: ["notifications", "list"] });
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [userId, queryClient]);
}

/** Full notification list for the notifications page. */
export function useNotifications(params?: { limit?: number; offset?: number }) {
  const getToken = useAuthToken();

  return useQuery<NotificationList, ApiError>({
    queryKey: QK.list(params),
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      const qs = new URLSearchParams();
      if (params?.limit) qs.set("limit", String(params.limit));
      if (params?.offset) qs.set("offset", String(params.offset));
      const q = qs.toString();
      return apiFetch<NotificationList>(`/api/notifications${q ? `?${q}` : ""}`, { token });
    },
    staleTime: 60 * 1000,
    retry: 1,
    throwOnError: false,
  });
}

/** Mark a single notification as read. */
export function useMarkNotificationRead() {
  const getToken = useAuthToken();
  const queryClient = useQueryClient();

  return useMutation<NotificationItem, ApiError, string>({
    mutationFn: async (notificationId) => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<NotificationItem>(`/api/notifications/${notificationId}/read`, {
        method: "PATCH",
        token,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

/** Mark all notifications as read. */
export function useMarkAllRead() {
  const getToken = useAuthToken();
  const queryClient = useQueryClient();

  return useMutation<UnreadCount, ApiError, void>({
    mutationFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<UnreadCount>("/api/notifications/read-all", {
        method: "PATCH",
        token,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}
