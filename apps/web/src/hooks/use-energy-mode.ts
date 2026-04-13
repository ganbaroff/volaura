"use client";

import { useState, useEffect, useCallback } from "react";

/**
 * Energy Mode hook — Constitution Law 2: Energy Adaptation
 *
 * Persistence: open-questions-resolved.md Q4
 * - Supabase profiles.energy_level (cross-device sync)
 * - localStorage volaura_energy_level (instant load cache)
 *
 * Three visual states (from open-questions-resolved.md):
 * - full: Standard UI, all animations, full information density
 * - mid: Reduce animations to opacity-only, larger touch targets (48px), hide secondary actions
 * - low: Single CTA per screen, max 3 elements visible, large text, zero animation, muted colors
 */

export type EnergyLevel = "full" | "mid" | "low";

const STORAGE_KEY = "volaura_energy_level";
const DEFAULT_ENERGY: EnergyLevel = "full";

export function useEnergyMode() {
  const [energy, setEnergyState] = useState<EnergyLevel>(DEFAULT_ENERGY);

  // Load from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as EnergyLevel | null;
    if (stored && ["full", "mid", "low"].includes(stored)) {
      setEnergyState(stored);
      document.documentElement.setAttribute("data-energy", stored);
    } else {
      document.documentElement.setAttribute("data-energy", DEFAULT_ENERGY);
    }
  }, []);

  const setEnergy = useCallback((level: EnergyLevel) => {
    setEnergyState(level);
    localStorage.setItem(STORAGE_KEY, level);
    document.documentElement.setAttribute("data-energy", level);

    // TODO: sync to Supabase profiles.energy_level when auth is available
    // await supabase.from('profiles').update({ energy_level: level }).eq('id', userId)
  }, []);

  return { energy, setEnergy } as const;
}
