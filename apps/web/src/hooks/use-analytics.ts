"use client";

import { useCallback } from "react";
import posthog from "posthog-js";
import { useAuthToken } from "./queries/use-auth-token";
import { API_BASE } from "@/lib/api/client";

/**
 * Fire-and-forget analytics event tracker.
 * Sends events to POST /api/analytics/event.
 * Never throws — analytics must not break user experience.
 *
 * Usage:
 *   const track = useTrackEvent();
 *   track("assessment_started", { competency_slug: "communication" });
 */
export function useTrackEvent() {
  const getToken = useAuthToken();

  return useCallback(
    async (
      eventName: string,
      properties?: Record<string, unknown>,
      sessionId?: string,
    ) => {
      const locale =
        typeof window !== "undefined"
          ? window.location.pathname.split("/")[1] || "en"
          : "en";

      try {
        const token = await getToken();
        if (!token) return; // not authenticated — skip silently

        await fetch(`${API_BASE}/analytics/event`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            event_name: eventName,
            properties: properties ?? {},
            session_id: sessionId,
            locale,
            platform: "web",
          }),
        });
      } catch {
        // Supabase analytics failure is silent — never blocks UX
      }

      try {
        if (typeof window !== "undefined" && posthog.__loaded) {
          posthog.capture(eventName, { ...properties, locale, session_id: sessionId });
        }
      } catch {
        // PostHog failure is silent — dual-write, Supabase is primary
      }
    },
    [getToken],
  );
}
