import { describe, it, expect, vi } from "vitest";
import { renderHook } from "@testing-library/react";

vi.mock("framer-motion", () => ({
  useReducedMotion: vi.fn(),
}));

import { useReducedMotion } from "framer-motion";
import { useMotionPreference } from "./use-reduced-motion";

const mockUseReducedMotion = vi.mocked(useReducedMotion);

describe("useMotionPreference", () => {
  it("returns spring transitions when motion is allowed", () => {
    mockUseReducedMotion.mockReturnValue(false);
    const { result } = renderHook(() => useMotionPreference());

    expect(result.current.shouldReduceMotion).toBe(false);
    expect(result.current.transition).toEqual({
      type: "spring",
      stiffness: 100,
      damping: 15,
    });
  });

  it("returns zero-duration transitions when motion is reduced", () => {
    mockUseReducedMotion.mockReturnValue(true);
    const { result } = renderHook(() => useMotionPreference());

    expect(result.current.shouldReduceMotion).toBe(true);
    expect(result.current.transition).toEqual({ duration: 0 });
  });

  it("returns entrance animation when motion allowed", () => {
    mockUseReducedMotion.mockReturnValue(false);
    const { result } = renderHook(() => useMotionPreference());

    expect(result.current.entrance.initial).toEqual({ opacity: 0, y: 20 });
    expect(result.current.entrance.animate).toEqual({ opacity: 1, y: 0 });
  });

  it("returns no-op entrance when motion reduced", () => {
    mockUseReducedMotion.mockReturnValue(true);
    const { result } = renderHook(() => useMotionPreference());

    expect(result.current.entrance.initial).toEqual({});
    expect(result.current.entrance.animate).toEqual({});
  });

  it("returns hover scale when motion allowed", () => {
    mockUseReducedMotion.mockReturnValue(false);
    const { result } = renderHook(() => useMotionPreference());

    expect(result.current.hoverScale).toEqual({ whileHover: { scale: 1.02 } });
  });

  it("returns no hover scale when motion reduced", () => {
    mockUseReducedMotion.mockReturnValue(true);
    const { result } = renderHook(() => useMotionPreference());

    expect(result.current.hoverScale).toEqual({});
  });

  it("returns tap scale when motion allowed", () => {
    mockUseReducedMotion.mockReturnValue(false);
    const { result } = renderHook(() => useMotionPreference());

    expect(result.current.tapScale).toEqual({ whileTap: { scale: 0.98 } });
  });

  it("returns no tap scale when motion reduced", () => {
    mockUseReducedMotion.mockReturnValue(true);
    const { result } = renderHook(() => useMotionPreference());

    expect(result.current.tapScale).toEqual({});
  });
});
