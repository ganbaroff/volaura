import { describe, it, expect, beforeEach } from "vitest";
import { readAndClearFromStorage, readAndClearAttribution } from "./utm-capture";

describe("readAndClearFromStorage", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("returns empty object when key absent", () => {
    expect(readAndClearFromStorage("nonexistent")).toEqual({});
  });

  it("parses valid JSON and removes key", () => {
    localStorage.setItem("test_key", JSON.stringify({ foo: "bar" }));
    const result = readAndClearFromStorage("test_key");
    expect(result).toEqual({ foo: "bar" });
    expect(localStorage.getItem("test_key")).toBeNull();
  });

  it("returns empty object for malformed JSON", () => {
    localStorage.setItem("bad_json", "{not valid json");
    expect(readAndClearFromStorage("bad_json")).toEqual({});
  });

  it("returns empty object for non-object JSON", () => {
    localStorage.setItem("str_val", '"just a string"');
    const result = readAndClearFromStorage("str_val");
    expect(result).toBe("just a string");
    expect(localStorage.getItem("str_val")).toBeNull();
  });
});

describe("readAndClearAttribution", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("returns empty object when no UTM params stored", () => {
    expect(readAndClearAttribution()).toEqual({});
  });

  it("reads ref and clears storage", () => {
    localStorage.setItem("volaura_ref", "friend123");
    const result = readAndClearAttribution();
    expect(result).toEqual({ referral_code: "friend123" });
    expect(localStorage.getItem("volaura_ref")).toBeNull();
  });

  it("reads utm_source and clears storage", () => {
    localStorage.setItem("volaura_utm_source", "linkedin");
    const result = readAndClearAttribution();
    expect(result).toEqual({ utm_source: "linkedin" });
    expect(localStorage.getItem("volaura_utm_source")).toBeNull();
  });

  it("reads utm_campaign and clears storage", () => {
    localStorage.setItem("volaura_utm_campaign", "launch_2026");
    const result = readAndClearAttribution();
    expect(result).toEqual({ utm_campaign: "launch_2026" });
    expect(localStorage.getItem("volaura_utm_campaign")).toBeNull();
  });

  it("reads all three params at once", () => {
    localStorage.setItem("volaura_ref", "ceo");
    localStorage.setItem("volaura_utm_source", "twitter");
    localStorage.setItem("volaura_utm_campaign", "beta");
    const result = readAndClearAttribution();
    expect(result).toEqual({
      referral_code: "ceo",
      utm_source: "twitter",
      utm_campaign: "beta",
    });
    expect(localStorage.getItem("volaura_ref")).toBeNull();
    expect(localStorage.getItem("volaura_utm_source")).toBeNull();
    expect(localStorage.getItem("volaura_utm_campaign")).toBeNull();
  });

  it("does not clear storage when no params present", () => {
    localStorage.setItem("unrelated_key", "keep_me");
    readAndClearAttribution();
    expect(localStorage.getItem("unrelated_key")).toBe("keep_me");
  });

  it("only clears attribution keys, not unrelated ones", () => {
    localStorage.setItem("volaura_ref", "x");
    localStorage.setItem("unrelated", "y");
    readAndClearAttribution();
    expect(localStorage.getItem("unrelated")).toBe("y");
  });
});
