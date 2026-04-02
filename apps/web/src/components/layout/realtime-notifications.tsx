"use client";

/**
 * RealtimeNotificationsProvider — subscribes to Supabase Realtime for
 * instant notification delivery without polling.
 *
 * Placed inside the dashboard layout so it persists across page navigation.
 * Reads the current user ID from Supabase auth (client-side, no server round-trip).
 *
 * Sprint C DSP winner: Supabase Realtime replaces polling for notification
 * count badge. Full WebSocket deferred to 2026-07-01 (DSP 2026-04-01).
 */

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { useRealtimeNotifications } from "@/hooks/queries/use-notifications";

export function RealtimeNotificationsProvider() {
  const [userId, setUserId] = useState<string | null>(null);

  // Get user ID from Supabase auth on mount — cheap read (cached session)
  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(({ data }) => {
      setUserId(data.user?.id ?? null);
    });
  }, []);

  // Subscribe once we have a userId — hook handles cleanup on unmount
  useRealtimeNotifications(userId);

  // Renders nothing — side-effect only
  return null;
}
