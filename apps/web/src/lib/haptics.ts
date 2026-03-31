/**
 * Haptic feedback utility for MindShift + VOLAURA
 *
 * Design principles (ADHD-first, research-backed — 2026-03-29):
 * - Every pulse ≤ 150ms: no "buzzy" vibrations (Android Design Principles)
 * - Short patterns, clear intent: streak_broken = ONE 30ms tap, not a punishment
 * - Respects user preference: haptics_enabled in localStorage
 * - iOS Safari limitation: Web Vibration API is NOT supported on any iOS browser.
 *   iOS gets silent no-op. Add ios-haptics library when Capacitor wrapper is added.
 *   See: https://caniuse.com/vibration
 *
 * Source: Doppel study PMC11285955 — rhythmic haptic patterns reduce ADHD anxiety
 * (state anxiety 56.43 → 43.40 over 8 weeks). Short predictable patterns = calming.
 */

export type HapticEvent =
  | "task_complete"       // Task done — two soft taps
  | "streak_maintained"   // Streak intact — ascending crescendo
  | "focus_start"         // Session beginning — single clean tap
  | "focus_end"           // Session over — balanced neutral
  | "streak_broken"       // Compassionate: ONE quiet tap, not a punishment buzz
  | "crystal_earned"      // Sparkle — 4 quick pulses, joyful
  | "gentle_reminder"     // Soft single — don't startle
  | "urgent"              // Clear three-tap alert — not anxiety-inducing
  | "error"               // Informative, asymmetric — NOT aggressive buzz
  | "level_up"            // Rare, celebratory crescendo — reserved for milestones
  | "badge_reveal";       // First time seeing AURA score — full reveal haptic

/**
 * Vibration patterns in milliseconds.
 * Format: [ON, off, ON, off, ON, ...]
 * Odd indices = vibrate duration. Even indices = silence duration.
 *
 * ADHD rule: no pulse > 150ms except level_up (reserved for rare milestone moments).
 * ADHD rule: never use a long unbroken buzz — it feels like "phone having a seizure."
 */
const PATTERNS: Record<HapticEvent, number[]> = {
  task_complete:     [40, 30, 80],                          // 150ms total
  streak_maintained: [30, 30, 50, 30, 80],                  // 220ms — ascending feel
  focus_start:       [60],                                  // 60ms — clean single
  focus_end:         [60, 60, 60],                          // 180ms — symmetric, neutral
  streak_broken:     [30],                                  // 30ms — ONE quiet tap only
  crystal_earned:    [30, 20, 30, 20, 50, 20, 80],          // 250ms — sparkle rhythm
  gentle_reminder:   [80],                                  // 80ms — soft, informative
  urgent:            [100, 80, 100, 80, 100],               // 460ms — clear, not anxious
  error:             [30, 30, 30, 30, 150],                 // 270ms — asymmetric, informative
  level_up:          [30, 20, 50, 20, 80, 20, 100, 20, 150], // 490ms — save for rare moments
  badge_reveal:      [50, 40, 80, 40, 120, 40, 80],         // 450ms — dramatic but not jarring
};

/**
 * Trigger a haptic event.
 *
 * Silently no-ops when:
 * - Vibration API is not supported (iOS, desktop)
 * - User has disabled haptics in settings (localStorage.haptics_enabled = "false")
 * - SSR / non-browser environment
 *
 * @param event - Named haptic event from the design system
 */
export function triggerHaptic(event: HapticEvent): void {
  // SSR guard
  if (typeof window === "undefined" || typeof navigator === "undefined") return;

  // User preference — stored in localStorage, defaults to enabled
  try {
    if (localStorage.getItem("haptics_enabled") === "false") return;
  } catch {
    // localStorage blocked (private browsing, sandboxed iframe) — silently skip
    return;
  }

  // Vibration API check — iOS Safari + desktop = graceful no-op
  if (!("vibrate" in navigator)) return;

  const pattern = PATTERNS[event];
  if (!pattern || pattern.length === 0) return;

  try {
    navigator.vibrate(pattern);
  } catch {
    // Some browsers throw if tab is not focused — silently ignore
  }
}

/**
 * Cancel any active haptic pattern.
 * Call this on component unmount or when stopping a focus session.
 */
export function cancelHaptic(): void {
  if (typeof navigator !== "undefined" && "vibrate" in navigator) {
    try {
      navigator.vibrate(0);
    } catch {
      // ignore
    }
  }
}

/**
 * Check if haptic feedback is supported and enabled on this device.
 * Use for conditional UI (e.g., showing the haptics settings toggle).
 */
export function isHapticsSupported(): boolean {
  return (
    typeof navigator !== "undefined" &&
    "vibrate" in navigator
  );
}

/**
 * Persistence helpers for the user haptics preference.
 * Used by the settings page toggle.
 */
export function setHapticsEnabled(enabled: boolean): void {
  try {
    localStorage.setItem("haptics_enabled", enabled ? "true" : "false");
  } catch {
    // ignore
  }
}

export function getHapticsEnabled(): boolean {
  try {
    return localStorage.getItem("haptics_enabled") !== "false";
  } catch {
    return true; // default: enabled
  }
}
