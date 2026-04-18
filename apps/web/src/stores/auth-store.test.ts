import { describe, it, expect, beforeEach } from "vitest";
import { useAuthStore } from "./auth-store";

describe("auth-store", () => {
  beforeEach(() => {
    useAuthStore.getState().clear();
  });

  it("starts with null user, null session, loading true", () => {
    useAuthStore.setState({ isLoading: true });
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.session).toBeNull();
    expect(state.isLoading).toBe(true);
  });

  it("setUser stores user", () => {
    const mockUser = { id: "u-1", email: "test@test.com" } as never;
    useAuthStore.getState().setUser(mockUser);
    expect(useAuthStore.getState().user).toEqual(mockUser);
  });

  it("setSession sets both session and user from session", () => {
    const mockUser = { id: "u-2", email: "a@b.com" };
    const mockSession = { user: mockUser, access_token: "tok" } as never;
    useAuthStore.getState().setSession(mockSession);
    const state = useAuthStore.getState();
    expect(state.session).toEqual(mockSession);
    expect(state.user).toEqual(mockUser);
  });

  it("setSession with null clears user", () => {
    const mockSession = { user: { id: "u-3" }, access_token: "tok" } as never;
    useAuthStore.getState().setSession(mockSession);
    useAuthStore.getState().setSession(null);
    const state = useAuthStore.getState();
    expect(state.session).toBeNull();
    expect(state.user).toBeNull();
  });

  it("setLoading toggles loading flag", () => {
    useAuthStore.getState().setLoading(false);
    expect(useAuthStore.getState().isLoading).toBe(false);
    useAuthStore.getState().setLoading(true);
    expect(useAuthStore.getState().isLoading).toBe(true);
  });

  it("clear resets all state", () => {
    const mockSession = { user: { id: "u-4" }, access_token: "t" } as never;
    useAuthStore.getState().setSession(mockSession);
    useAuthStore.getState().setLoading(true);

    useAuthStore.getState().clear();

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.session).toBeNull();
    expect(state.isLoading).toBe(false);
  });
});
