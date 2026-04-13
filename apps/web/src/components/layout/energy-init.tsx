"use client";

import { useEffect } from "react";
import { useEnergyMode } from "@/hooks/use-energy-mode";

/**
 * EnergyInit — silent client component that syncs energy mode to <html>
 *
 * Place once in any layout. Reads localStorage on mount and sets
 * data-energy attribute so all CSS energy tokens activate.
 *
 * Constitution Law 2: energy adaptation must be immediate on page load.
 */
export function EnergyInit() {
  const { energy } = useEnergyMode();

  useEffect(() => {
    // useEnergyMode already sets the attribute, but ensure it's set
    // even if the hook runs before the DOM is ready
    document.documentElement.setAttribute("data-energy", energy);
  }, [energy]);

  return null;
}
