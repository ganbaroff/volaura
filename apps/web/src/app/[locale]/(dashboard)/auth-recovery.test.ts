import { describe, expect, it } from "vitest";
import { buildLoginNextPath } from "./auth-recovery";

describe("buildLoginNextPath", () => {
  it("keeps locale and encodes target path", () => {
    expect(buildLoginNextPath("en", "/en/dashboard")).toBe("/en/login?next=%2Fen%2Fdashboard");
  });

  it("encodes nested dashboard paths with query params", () => {
    expect(buildLoginNextPath("az", "/az/aura?tab=score")).toBe(
      "/az/login?next=%2Faz%2Faura%3Ftab%3Dscore"
    );
  });
});
