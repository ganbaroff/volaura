import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import type { EnergyLevel } from "./use-energy-mode";

const mockFrom = vi.fn();
const mockGetUser = vi.fn();

vi.mock("@/lib/supabase/client", () => ({
  createClient: () => ({
    auth: { getUser: mockGetUser },
    from: mockFrom,
  }),
}));

describe("useEnergyMode", () => {
  let localStorageMock: Record<string, string>;

  beforeEach(() => {
    vi.resetModules();
    localStorageMock = {};

    vi.stubGlobal("localStorage", {
      getItem: vi.fn((key: string) => localStorageMock[key] ?? null),
      setItem: vi.fn((key: string, value: string) => {
        localStorageMock[key] = value;
      }),
      removeItem: vi.fn((key: string) => {
        delete localStorageMock[key];
      }),
    });

    document.documentElement.setAttribute("data-energy", "");
    mockGetUser.mockResolvedValue({ data: { user: null } });
    mockFrom.mockReturnValue({
      select: vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          maybeSingle: vi.fn().mockResolvedValue({ data: null }),
        }),
      }),
      update: vi.fn().mockReturnValue({
        eq: vi.fn().mockResolvedValue({ data: null }),
      }),
    });
  });

  async function getHook() {
    const mod = await import("./use-energy-mode");
    return renderHook(() => mod.useEnergyMode());
  }

  it("defaults to 'full' when localStorage is empty", async () => {
    const { result } = await getHook();
    expect(result.current.energy).toBe("full");
  });

  it("reads stored energy level from localStorage on mount", async () => {
    localStorageMock["volaura_energy_level"] = "low";
    const { result, rerender } = await getHook();
    rerender();
    await vi.waitFor(() => {
      expect(result.current.energy).toBe("low");
    });
  });

  it("sets data-energy attribute on documentElement", async () => {
    localStorageMock["volaura_energy_level"] = "mid";
    await getHook();
    await vi.waitFor(() => {
      expect(document.documentElement.getAttribute("data-energy")).toBe("mid");
    });
  });

  it("ignores invalid localStorage values", async () => {
    localStorageMock["volaura_energy_level"] = "turbo";
    const { result } = await getHook();
    await vi.waitFor(() => {
      expect(result.current.energy).toBe("full");
      expect(document.documentElement.getAttribute("data-energy")).toBe("full");
    });
  });

  it("setEnergy updates state, localStorage, and data-energy attribute", async () => {
    const { result } = await getHook();

    act(() => {
      result.current.setEnergy("low");
    });

    expect(result.current.energy).toBe("low");
    expect(localStorage.setItem).toHaveBeenCalledWith(
      "volaura_energy_level",
      "low"
    );
    expect(document.documentElement.getAttribute("data-energy")).toBe("low");
  });

  it("setEnergy cycles through all three levels", async () => {
    const { result } = await getHook();
    const levels: EnergyLevel[] = ["full", "mid", "low"];

    for (const level of levels) {
      act(() => {
        result.current.setEnergy(level);
      });
      expect(result.current.energy).toBe(level);
      expect(document.documentElement.getAttribute("data-energy")).toBe(level);
    }
  });

  it("reconciles with server value when user is signed in", async () => {
    localStorageMock["volaura_energy_level"] = "full";
    mockGetUser.mockResolvedValue({
      data: { user: { id: "user-123" } },
    });
    mockFrom.mockReturnValue({
      select: vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          maybeSingle: vi
            .fn()
            .mockResolvedValue({ data: { energy_level: "low" } }),
        }),
      }),
      update: vi.fn().mockReturnValue({
        eq: vi.fn().mockResolvedValue({ data: null }),
      }),
    });

    const { result } = await getHook();

    await vi.waitFor(() => {
      expect(result.current.energy).toBe("low");
    });
    expect(localStorage.setItem).toHaveBeenCalledWith(
      "volaura_energy_level",
      "low"
    );
  });

  it("does not reconcile when server returns null", async () => {
    localStorageMock["volaura_energy_level"] = "mid";
    mockGetUser.mockResolvedValue({
      data: { user: { id: "user-123" } },
    });
    mockFrom.mockReturnValue({
      select: vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          maybeSingle: vi.fn().mockResolvedValue({ data: null }),
        }),
      }),
      update: vi.fn().mockReturnValue({
        eq: vi.fn().mockResolvedValue({ data: null }),
      }),
    });

    const { result } = await getHook();
    await vi.waitFor(() => {
      expect(result.current.energy).toBe("mid");
    });
  });

  it("does not reconcile when server value matches local", async () => {
    localStorageMock["volaura_energy_level"] = "mid";
    mockGetUser.mockResolvedValue({
      data: { user: { id: "user-123" } },
    });
    mockFrom.mockReturnValue({
      select: vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          maybeSingle: vi
            .fn()
            .mockResolvedValue({ data: { energy_level: "mid" } }),
        }),
      }),
      update: vi.fn().mockReturnValue({
        eq: vi.fn().mockResolvedValue({ data: null }),
      }),
    });

    const { result } = await getHook();
    await vi.waitFor(() => {
      expect(result.current.energy).toBe("mid");
    });
  });

  it("fires Supabase update on setEnergy when user is signed in", async () => {
    const mockUpdate = vi.fn().mockReturnValue({
      eq: vi.fn().mockResolvedValue({ data: null }),
    });
    mockGetUser.mockResolvedValue({
      data: { user: { id: "user-456" } },
    });
    mockFrom.mockReturnValue({
      select: vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          maybeSingle: vi.fn().mockResolvedValue({ data: null }),
        }),
      }),
      update: mockUpdate,
    });

    const { result } = await getHook();

    act(() => {
      result.current.setEnergy("mid");
    });

    await vi.waitFor(() => {
      expect(mockUpdate).toHaveBeenCalledWith({ energy_level: "mid" });
    });
  });

  it("does not call Supabase update when user is not signed in", async () => {
    mockGetUser.mockResolvedValue({ data: { user: null } });
    const mockUpdate = vi.fn();
    mockFrom.mockReturnValue({
      select: vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          maybeSingle: vi.fn().mockResolvedValue({ data: null }),
        }),
      }),
      update: mockUpdate,
    });

    const { result } = await getHook();

    act(() => {
      result.current.setEnergy("low");
    });

    await vi.waitFor(() => {
      expect(result.current.energy).toBe("low");
    });
    expect(mockUpdate).not.toHaveBeenCalled();
  });
});
