import { describe, expect, it } from "vitest";
import { ApiError } from "@/lib/api/client";
import { getDiscoverBrowseErrorState, getDiscoverSearchErrorState } from "./error-state";

describe("discover error state", () => {
  it("maps browse 401 to reauth state", () => {
    expect(getDiscoverBrowseErrorState(new ApiError(401, "UNAUTHORIZED", "expired"))).toEqual({
      title: "Session expired",
      description: "Please sign in again to continue talent discovery.",
      actionLabel: "Sign in again",
      action: "login",
    });
  });

  it("maps browse 403 to org-only state", () => {
    expect(getDiscoverBrowseErrorState(new ApiError(403, "FORBIDDEN", "forbidden"))).toEqual({
      title: "Organization access required",
      description: "Talent discovery is available to organization accounts only.",
      actionLabel: null,
      action: null,
    });
  });

  it("maps browse server failures to retry state", () => {
    expect(getDiscoverBrowseErrorState(new ApiError(500, "SERVER_ERROR", "boom"))).toEqual({
      title: "Could not load professionals",
      description: "Please try again.",
      actionLabel: "Retry",
      action: "retry",
    });
  });

  it("maps search 401 to reauth state", () => {
    expect(getDiscoverSearchErrorState(new ApiError(401, "UNAUTHORIZED", "expired"))).toEqual({
      title: "Session expired",
      description: "Please sign in again to continue smart search.",
      actionLabel: "Sign in again",
      action: "login",
    });
  });

  it("maps search 403 to org-only state", () => {
    expect(getDiscoverSearchErrorState(new ApiError(403, "FORBIDDEN", "forbidden"))).toEqual({
      title: "Organization access required",
      description: "Smart search is available to organization accounts only.",
      actionLabel: null,
      action: null,
    });
  });
});
