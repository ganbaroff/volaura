/**
 * Tests for onboarding draft storage (Task 4, UX-LOGIC-AUDIT-2026-04-18 #4).
 *
 * jsdom gives us a real sessionStorage. We clear between tests so state
 * doesn't leak between cases.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  ONBOARDING_DRAFT_KEY,
  ONBOARDING_DRAFT_TTL_MS,
  clearOnboardingDraft,
  readOnboardingDraft,
  writeOnboardingDraft,
  type OnboardingDraft,
} from "./draft-storage";

const sampleFormData = {
  display_name: "Leyla",
  username: "leyla_az",
  location: "Baku",
  languages: ["Azerbaijani", "English"],
  selectedCompetency: "communication",
  visible_to_orgs: true,
};

describe("onboarding draft storage", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    vi.useRealTimers();
  });

  afterEach(() => {
    window.sessionStorage.clear();
  });

  it("returns null when no draft present", () => {
    expect(readOnboardingDraft()).toBeNull();
  });

  it("round-trips a valid draft", () => {
    writeOnboardingDraft({ step: 3, accountType: "professional", formData: sampleFormData });
    const read = readOnboardingDraft();
    expect(read).not.toBeNull();
    expect(read?.step).toBe(3);
    expect(read?.accountType).toBe("professional");
    expect(read?.formData).toEqual(sampleFormData);
    expect(read?.v).toBe(1);
    expect(typeof read?.savedAt).toBe("number");
  });

  it("clear wipes the draft", () => {
    writeOnboardingDraft({ step: 2, accountType: "professional", formData: sampleFormData });
    expect(readOnboardingDraft()).not.toBeNull();
    clearOnboardingDraft();
    expect(readOnboardingDraft()).toBeNull();
  });

  it("drops drafts older than the TTL", () => {
    const stale: OnboardingDraft = {
      v: 1,
      step: 3,
      accountType: "professional",
      formData: sampleFormData,
      savedAt: Date.now() - ONBOARDING_DRAFT_TTL_MS - 1000,
    };
    window.sessionStorage.setItem(ONBOARDING_DRAFT_KEY, JSON.stringify(stale));
    expect(readOnboardingDraft()).toBeNull();
    // Stale read also evicts the entry to keep sessionStorage clean.
    expect(window.sessionStorage.getItem(ONBOARDING_DRAFT_KEY)).toBeNull();
  });

  it("rejects drafts with wrong schema version", () => {
    window.sessionStorage.setItem(
      ONBOARDING_DRAFT_KEY,
      JSON.stringify({ ...{ v: 2, step: 1, accountType: "professional", formData: sampleFormData, savedAt: Date.now() } }),
    );
    expect(readOnboardingDraft()).toBeNull();
  });

  it("rejects corrupt JSON", () => {
    window.sessionStorage.setItem(ONBOARDING_DRAFT_KEY, "{ this is not json");
    expect(readOnboardingDraft()).toBeNull();
  });

  it("rejects drafts with an unexpected accountType", () => {
    window.sessionStorage.setItem(
      ONBOARDING_DRAFT_KEY,
      JSON.stringify({ v: 1, step: 1, accountType: "admin", formData: sampleFormData, savedAt: Date.now() }),
    );
    expect(readOnboardingDraft()).toBeNull();
  });

  it("rejects drafts where formData is missing a required field", () => {
    const badFormData = { ...sampleFormData, languages: undefined as unknown as string[] };
    window.sessionStorage.setItem(
      ONBOARDING_DRAFT_KEY,
      JSON.stringify({ v: 1, step: 2, accountType: "professional", formData: badFormData, savedAt: Date.now() }),
    );
    expect(readOnboardingDraft()).toBeNull();
  });

  it("preserves organization accountType through round-trip", () => {
    writeOnboardingDraft({
      step: 2,
      accountType: "organization",
      formData: { ...sampleFormData, selectedCompetency: "" },
    });
    const read = readOnboardingDraft();
    expect(read?.accountType).toBe("organization");
    expect(read?.step).toBe(2);
  });
});
