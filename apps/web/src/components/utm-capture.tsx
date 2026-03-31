"use client";

/**
 * UTMCapture — silently reads UTM/referral params from URL and persists to localStorage.
 * Included in root layout so it fires on any page entry point (landing, direct share links, etc.).
 * Callback page reads these keys and writes them to the user profile on first auth.
 */

import { useEffect } from "react";
import { useSearchParams } from "next/navigation";

const STORAGE_KEYS = {
  ref: "volaura_ref",
  utm_source: "volaura_utm_source",
  utm_campaign: "volaura_utm_campaign",
} as const;

function UTMCaptureInner() {
  const searchParams = useSearchParams();

  useEffect(() => {
    const ref = searchParams.get("ref");
    const utmSource = searchParams.get("utm_source");
    const utmCampaign = searchParams.get("utm_campaign");

    // Only write if present in URL — never overwrite existing values with nulls
    if (ref) localStorage.setItem(STORAGE_KEYS.ref, ref);
    if (utmSource) localStorage.setItem(STORAGE_KEYS.utm_source, utmSource);
    if (utmCampaign) localStorage.setItem(STORAGE_KEYS.utm_campaign, utmCampaign);
  }, [searchParams]);

  return null;
}

// Wrapped in Suspense boundary because useSearchParams requires it
import { Suspense } from "react";

export function UTMCapture() {
  return (
    <Suspense fallback={null}>
      <UTMCaptureInner />
    </Suspense>
  );
}

/**
 * Generic: reads a JSON object from localStorage, removes the key, returns the value.
 * Returns {} if key is absent, JSON is invalid, or called server-side.
 */
export function readAndClearFromStorage(key: string): Record<string, string> {
  if (typeof window === "undefined") return {};
  try {
    const raw = localStorage.getItem(key);
    if (raw) {
      const data = JSON.parse(raw) as Record<string, string>;
      localStorage.removeItem(key);
      return data;
    }
  } catch {
    // Ignore malformed data
  }
  return {};
}

/**
 * Reads attribution from localStorage, returns an object with non-null values only.
 * Used by the auth callback to PATCH the profile after successful sign-in.
 */
export function readAndClearAttribution(): Record<string, string> {
  if (typeof window === "undefined") return {};

  const result: Record<string, string> = {};
  const ref = localStorage.getItem(STORAGE_KEYS.ref);
  const utmSource = localStorage.getItem(STORAGE_KEYS.utm_source);
  const utmCampaign = localStorage.getItem(STORAGE_KEYS.utm_campaign);

  if (ref) result.referral_code = ref;
  if (utmSource) result.utm_source = utmSource;
  if (utmCampaign) result.utm_campaign = utmCampaign;

  // Clear immediately to avoid re-sending on subsequent sign-ins
  if (Object.keys(result).length > 0) {
    localStorage.removeItem(STORAGE_KEYS.ref);
    localStorage.removeItem(STORAGE_KEYS.utm_source);
    localStorage.removeItem(STORAGE_KEYS.utm_campaign);
  }

  return result;
}
