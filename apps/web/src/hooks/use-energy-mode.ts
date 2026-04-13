"use client";

import { useState, useEffect, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";

/**
 * Energy Mode hook — Constitution Law 2: Energy Adaptation
 *
 * Persistence:
 * - localStorage `volaura_energy_level` — instant load cache, works offline / signed out
 * - Supabase `profiles.energy_level` — cross-device sync, best-effort (auth required)
 *
 * Three visual states:
 * - full: Standard UI, all animations, full information density
 * - mid: Reduce animations to opacity-only, larger touch targets (48px), hide secondary actions
 * - low: Single CTA per screen, max 3 elements visible, large text, zero animation, muted colors
 */

export type EnergyLevel = "full" | "mid" | "low";

const STORAGE_KEY = "volaura_energy_level";
const DEFAULT_ENERGY: EnergyLevel = "full";

export function useEnergyMode() {
  const [energy, setEnergyState] = useState<EnergyLevel>(DEFAULT_ENERGY);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as EnergyLevel | null;
    if (stored && ["full", "mid", "low"].includes(stored)) {
      setEnergyState(stored);
      document.documentElement.setAttribute("data-energy", stored);
    } else {
      document.documentElement.setAttribute("data-energy", DEFAULT_ENERGY);
    }

    // Best-effort: if signed in, pull the authoritative value from profiles and
    // reconcile — server wins on conflict (user picked "low" on phone yesterday,
    // opens desktop with stale "full" in localStorage → desktop updates to "low").
    const supabase = createClient();
    supabase.auth.getUser().then(({ data }) => {
      const userId = data?.user?.id;
      if (!userId) return;
      supabase
        .from("profiles")
        .select("energy_level")
        .eq("id", userId)
        .maybeSingle()
        .then(({ data: row }) => {
          const serverLevel = row?.energy_level as EnergyLevel | null | undefined;
          if (serverLevel && ["full", "mid", "low"].includes(serverLevel) && serverLevel !== stored) {
            setEnergyState(serverLevel);
            localStorage.setItem(STORAGE_KEY, serverLevel);
            document.documentElement.setAttribute("data-energy", serverLevel);
          }
        });
    });
  }, []);

  const setEnergy = useCallback((level: EnergyLevel) => {
    setEnergyState(level);
    localStorage.setItem(STORAGE_KEY, level);
    document.documentElement.setAttribute("data-energy", level);

    // Fire-and-forget to Supabase — UI never waits on the network for mode switch.
    const supabase = createClient();
    supabase.auth.getUser().then(({ data }) => {
      const userId = data?.user?.id;
      if (!userId) return;
      void supabase
        .from("profiles")
        .update({ energy_level: level })
        .eq("id", userId);
    });
  }, []);

  return { energy, setEnergy } as const;
}
