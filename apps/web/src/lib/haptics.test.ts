import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  triggerHaptic,
  cancelHaptic,
  isHapticsSupported,
  setHapticsEnabled,
  getHapticsEnabled,
  type HapticEvent,
} from "./haptics";

describe("haptics", () => {
  let vibrateSpy: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vibrateSpy = vi.fn();
    Object.defineProperty(navigator, "vibrate", {
      value: vibrateSpy,
      writable: true,
      configurable: true,
    });
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("PATTERNS design rules", () => {
    const ALL_EVENTS: HapticEvent[] = [
      "task_complete",
      "streak_maintained",
      "focus_start",
      "focus_end",
      "streak_broken",
      "crystal_earned",
      "gentle_reminder",
      "urgent",
      "error",
      "level_up",
      "badge_reveal",
    ];

    it("no pulse exceeds 150ms except level_up", () => {
      for (const event of ALL_EVENTS) {
        triggerHaptic(event);
        const pattern = vibrateSpy.mock.lastCall?.[0] as number[];
        if (!pattern) continue;
        for (let i = 0; i < pattern.length; i += 2) {
          if (event === "level_up") continue;
          expect(pattern[i]).toBeLessThanOrEqual(150);
        }
        vibrateSpy.mockClear();
      }
    });

    it("all 11 haptic events trigger vibrate", () => {
      for (const event of ALL_EVENTS) {
        triggerHaptic(event);
        expect(vibrateSpy).toHaveBeenCalled();
        vibrateSpy.mockClear();
      }
    });

    it("streak_broken is a single quiet tap (30ms)", () => {
      triggerHaptic("streak_broken");
      expect(vibrateSpy).toHaveBeenCalledWith([30]);
    });
  });

  describe("triggerHaptic", () => {
    it("calls navigator.vibrate with the correct pattern", () => {
      triggerHaptic("focus_start");
      expect(vibrateSpy).toHaveBeenCalledWith([60]);
    });

    it("skips when haptics_enabled is false", () => {
      localStorage.setItem("haptics_enabled", "false");
      triggerHaptic("focus_start");
      expect(vibrateSpy).not.toHaveBeenCalled();
    });

    it("fires when haptics_enabled is true", () => {
      localStorage.setItem("haptics_enabled", "true");
      triggerHaptic("focus_start");
      expect(vibrateSpy).toHaveBeenCalled();
    });

    it("fires when haptics_enabled is not set (default enabled)", () => {
      triggerHaptic("focus_start");
      expect(vibrateSpy).toHaveBeenCalled();
    });

    it("no-ops when vibrate is not in navigator", () => {
      delete (navigator as unknown as Record<string, unknown>).vibrate;
      expect(() => triggerHaptic("focus_start")).not.toThrow();
    });

    it("swallows vibrate exceptions silently", () => {
      vibrateSpy.mockImplementation(() => {
        throw new Error("Tab not focused");
      });
      expect(() => triggerHaptic("focus_start")).not.toThrow();
    });
  });

  describe("cancelHaptic", () => {
    it("calls navigator.vibrate(0)", () => {
      cancelHaptic();
      expect(vibrateSpy).toHaveBeenCalledWith(0);
    });
  });

  describe("isHapticsSupported", () => {
    it("returns true when vibrate exists", () => {
      expect(isHapticsSupported()).toBe(true);
    });

    it("returns false when vibrate is absent", () => {
      delete (navigator as unknown as Record<string, unknown>).vibrate;
      expect(isHapticsSupported()).toBe(false);
    });
  });

  describe("setHapticsEnabled / getHapticsEnabled", () => {
    it("defaults to true", () => {
      expect(getHapticsEnabled()).toBe(true);
    });

    it("persists false", () => {
      setHapticsEnabled(false);
      expect(getHapticsEnabled()).toBe(false);
      expect(localStorage.getItem("haptics_enabled")).toBe("false");
    });

    it("persists true", () => {
      setHapticsEnabled(true);
      expect(getHapticsEnabled()).toBe(true);
      expect(localStorage.getItem("haptics_enabled")).toBe("true");
    });

    it("round-trips correctly", () => {
      setHapticsEnabled(false);
      expect(getHapticsEnabled()).toBe(false);
      setHapticsEnabled(true);
      expect(getHapticsEnabled()).toBe(true);
    });
  });
});
