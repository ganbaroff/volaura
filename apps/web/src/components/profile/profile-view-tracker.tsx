"use client";

import { useEffect } from "react";
import { createClient } from "@/lib/supabase/client";
import { apiFetch, API_BASE } from "@/lib/api/client";

/**
 * ProfileViewTracker — fires POST /api/profiles/{username}/view on mount.
 *
 * This notifies the volunteer when an authenticated org views their profile.
 * Rendered silently (no UI output). Safe to include in any public profile page.
 *
 * Behavior:
 * - Only fires if the viewer has an active Supabase session (logged in)
 * - The backend deduplicates: at most 1 notification per (org, volunteer) per 24h
 * - Non-org viewers: backend silently returns 204 with no notification sent
 * - Any error is swallowed — never blocks page rendering
 */
export function ProfileViewTracker({ username }: { username: string }) {
  useEffect(() => {
    let cancelled = false;

    async function recordView() {
      try {
        const supabase = createClient();
        const { data: { session } } = await supabase.auth.getSession();
        if (!session || cancelled) return; // not logged in — skip

        await apiFetch(`/api/profiles/${username}/view`, {
          method: "POST",
          token: session.access_token,
        });

        // Analytics: profile_viewed (fire-and-forget)
        fetch(`${API_BASE}/analytics/event`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${session.access_token}`,
          },
          body: JSON.stringify({
            event_name: "profile_viewed",
            properties: { viewed_username: username },
            platform: "web",
          }),
        }).catch(() => {});
      } catch {
        // fire-and-forget — swallow all errors
      }
    }

    recordView();
    return () => { cancelled = true; };
  }, [username]);

  return null;
}
