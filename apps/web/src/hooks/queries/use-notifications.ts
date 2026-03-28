"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuthToken } from "./use-auth-token";
import { apiFetch, ApiError } from "@/lib/api/client";

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

/** Unread count — used for sidebar badge. Polls every 2 min. */
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
