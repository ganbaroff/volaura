import { describe, expect, it } from "vitest";
import { getCallbackProfileRoute } from "./route-decision";

describe("callback profile route decision", () => {
  it("routes missing profile to onboarding", () => {
    expect(getCallbackProfileRoute("en", 404)).toBe("/en/onboarding");
  });

  it("routes successful profile lookup to dashboard", () => {
    expect(getCallbackProfileRoute("az", 200)).toBe("/az/dashboard");
  });

  it("routes auth failures to explicit oauth error", () => {
    expect(getCallbackProfileRoute("en", 401)).toBe("/en/login?message=oauth-error");
  });

  it("routes server failures to explicit oauth error", () => {
    expect(getCallbackProfileRoute("en", 500)).toBe("/en/login?message=oauth-error");
  });

  it("routes network failures to explicit oauth error", () => {
    expect(getCallbackProfileRoute("en", "network-error")).toBe("/en/login?message=oauth-error");
  });
});
