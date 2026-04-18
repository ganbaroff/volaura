import { describe, it, expect } from "vitest";
import { cn } from "./cn";

describe("cn", () => {
  it("merges simple class names", () => {
    expect(cn("foo", "bar")).toBe("foo bar");
  });

  it("handles conditional classes via clsx", () => {
    expect(cn("base", false && "hidden", "visible")).toBe("base visible");
  });

  it("merges conflicting Tailwind classes (last wins)", () => {
    expect(cn("p-4", "p-2")).toBe("p-2");
  });

  it("merges conflicting color classes", () => {
    expect(cn("text-red-500", "text-blue-500")).toBe("text-blue-500");
  });

  it("handles undefined and null inputs", () => {
    expect(cn("base", undefined, null, "end")).toBe("base end");
  });

  it("handles empty string", () => {
    expect(cn("", "foo")).toBe("foo");
  });

  it("handles array inputs", () => {
    expect(cn(["foo", "bar"], "baz")).toBe("foo bar baz");
  });

  it("handles object inputs", () => {
    expect(cn({ "bg-red-500": true, "bg-blue-500": false })).toBe(
      "bg-red-500"
    );
  });

  it("returns empty string for no inputs", () => {
    expect(cn()).toBe("");
  });

  it("preserves non-conflicting Tailwind classes", () => {
    expect(cn("p-4", "m-2", "text-lg")).toBe("p-4 m-2 text-lg");
  });

  it("handles responsive variants correctly", () => {
    expect(cn("md:p-4", "md:p-8")).toBe("md:p-8");
  });
});
