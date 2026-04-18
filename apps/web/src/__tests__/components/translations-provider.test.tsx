import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";

// ── Hoisted mocks ─────────────────────────────────────────────────────────────

const {
  mockCreateInstance,
  mockInit,
  mockUse,
  mockResourcesToBackend,
  mockInitReactI18next,
  mockI18nextProvider,
  capturedInitOptions,
  usedPlugins,
} = vi.hoisted(() => {
  const capturedInitOptions: { value: Record<string, unknown> } = { value: {} };
  const usedPlugins: { list: unknown[] } = { list: [] };

  const mockInit = vi.fn((options: Record<string, unknown>) => {
    capturedInitOptions.value = options;
  });

  const mockUse = vi.fn((plugin: unknown) => {
    usedPlugins.list.push(plugin);
    return { use: mockUse, init: mockInit };
  });

  const mockI18nInstance = { use: mockUse, init: mockInit };
  const mockCreateInstance = vi.fn(() => mockI18nInstance);

  const mockInitReactI18next = { type: "3rdParty" as const, name: "initReactI18next" };
  const mockResourcesToBackend = vi.fn(() => ({ type: "backend", name: "resourcesToBackend" }));

  const mockI18nextProvider = vi.fn(({ children }: { children: React.ReactNode }) => (
    <div data-testid="i18next-provider">{children}</div>
  ));

  return {
    mockCreateInstance,
    mockInit,
    mockUse,
    mockResourcesToBackend,
    mockInitReactI18next,
    mockI18nextProvider,
    capturedInitOptions,
    usedPlugins,
  };
});

vi.mock("@/i18nConfig", () => ({
  default: {
    locales: ["az", "en"],
    defaultLocale: "az",
    prefixDefault: true,
  },
}));

vi.mock("i18next", () => ({
  createInstance: mockCreateInstance,
}));

vi.mock("react-i18next/initReactI18next", () => ({
  initReactI18next: mockInitReactI18next,
}));

vi.mock("i18next-resources-to-backend", () => ({
  default: mockResourcesToBackend,
}));

vi.mock("react-i18next", () => ({
  I18nextProvider: (props: { children: React.ReactNode; i18n: unknown }) =>
    mockI18nextProvider(props),
}));

// ── Import after mocks ────────────────────────────────────────────────────────

import TranslationsProvider from "@/components/translations-provider";

// ── Helpers ───────────────────────────────────────────────────────────────────

function makeResources() {
  return {
    az: { common: { hello: "Salam" } },
    en: { common: { hello: "Hello" } },
  };
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("TranslationsProvider — rendering", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    capturedInitOptions.value = {};
    usedPlugins.list = [];
    mockUse.mockImplementation((plugin: unknown) => {
      usedPlugins.list.push(plugin);
      return { use: mockUse, init: mockInit };
    });
  });

  it("renders children", () => {
    render(
      <TranslationsProvider locale="az" namespaces={["common"]} resources={makeResources()}>
        <div>child content</div>
      </TranslationsProvider>
    );
    expect(screen.getByText("child content")).toBeInTheDocument();
  });

  it("wraps children in I18nextProvider", () => {
    render(
      <TranslationsProvider locale="az" namespaces={["common"]} resources={makeResources()}>
        <span>inner</span>
      </TranslationsProvider>
    );
    expect(screen.getByTestId("i18next-provider")).toBeInTheDocument();
  });
});

describe("TranslationsProvider — i18next instance creation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    capturedInitOptions.value = {};
    usedPlugins.list = [];
    mockUse.mockImplementation((plugin: unknown) => {
      usedPlugins.list.push(plugin);
      return { use: mockUse, init: mockInit };
    });
  });

  it("creates a new i18next instance on each render", () => {
    render(
      <TranslationsProvider locale="az" namespaces={["common"]} resources={makeResources()}>
        <div>child</div>
      </TranslationsProvider>
    );
    expect(mockCreateInstance).toHaveBeenCalled();
  });

  it("uses initReactI18next plugin", () => {
    render(
      <TranslationsProvider locale="az" namespaces={["common"]} resources={makeResources()}>
        <div>child</div>
      </TranslationsProvider>
    );
    expect(usedPlugins.list).toContain(mockInitReactI18next);
  });

  it("uses resourcesToBackend plugin", () => {
    render(
      <TranslationsProvider locale="az" namespaces={["common"]} resources={makeResources()}>
        <div>child</div>
      </TranslationsProvider>
    );
    expect(mockResourcesToBackend).toHaveBeenCalled();
    const backendPlugin = mockResourcesToBackend.mock.results[0].value;
    expect(usedPlugins.list).toContain(backendPlugin);
  });
});

describe("TranslationsProvider — init options", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    capturedInitOptions.value = {};
    usedPlugins.list = [];
    mockUse.mockImplementation((plugin: unknown) => {
      usedPlugins.list.push(plugin);
      return { use: mockUse, init: mockInit };
    });
  });

  it("initializes with the correct locale from props", () => {
    render(
      <TranslationsProvider locale="en" namespaces={["common"]} resources={makeResources()}>
        <div>child</div>
      </TranslationsProvider>
    );
    expect(capturedInitOptions.value.lng).toBe("en");
  });

  it("uses az as fallbackLng from i18nConfig.defaultLocale", () => {
    render(
      <TranslationsProvider locale="en" namespaces={["common"]} resources={makeResources()}>
        <div>child</div>
      </TranslationsProvider>
    );
    expect(capturedInitOptions.value.fallbackLng).toBe("az");
  });

  it("supportedLngs matches i18nConfig.locales", () => {
    render(
      <TranslationsProvider locale="az" namespaces={["common"]} resources={makeResources()}>
        <div>child</div>
      </TranslationsProvider>
    );
    expect(capturedInitOptions.value.supportedLngs).toEqual(["az", "en"]);
  });

  it("defaultNS is the first namespace from props", () => {
    render(
      <TranslationsProvider
        locale="az"
        namespaces={["common", "auth"]}
        resources={makeResources()}
      >
        <div>child</div>
      </TranslationsProvider>
    );
    expect(capturedInitOptions.value.defaultNS).toBe("common");
  });

  it("fallbackNS is the first namespace from props", () => {
    render(
      <TranslationsProvider
        locale="az"
        namespaces={["common", "auth"]}
        resources={makeResources()}
      >
        <div>child</div>
      </TranslationsProvider>
    );
    expect(capturedInitOptions.value.fallbackNS).toBe("common");
  });

  it("initImmediate is false for synchronous SSR init", () => {
    render(
      <TranslationsProvider locale="az" namespaces={["common"]} resources={makeResources()}>
        <div>child</div>
      </TranslationsProvider>
    );
    expect(capturedInitOptions.value.initImmediate).toBe(false);
  });

  it("passes resources through to i18next init", () => {
    const resources = makeResources();
    render(
      <TranslationsProvider locale="az" namespaces={["common"]} resources={resources}>
        <div>child</div>
      </TranslationsProvider>
    );
    expect(capturedInitOptions.value.resources).toBe(resources);
  });

  it("passes all namespaces to ns option", () => {
    render(
      <TranslationsProvider
        locale="az"
        namespaces={["common", "auth", "profile"]}
        resources={makeResources()}
      >
        <div>child</div>
      </TranslationsProvider>
    );
    expect(capturedInitOptions.value.ns).toEqual(["common", "auth", "profile"]);
  });

  it("handles multiple namespaces with correct defaultNS and fallbackNS", () => {
    render(
      <TranslationsProvider
        locale="az"
        namespaces={["dashboard", "common", "auth"]}
        resources={makeResources()}
      >
        <div>child</div>
      </TranslationsProvider>
    );
    expect(capturedInitOptions.value.defaultNS).toBe("dashboard");
    expect(capturedInitOptions.value.fallbackNS).toBe("dashboard");
    expect(capturedInitOptions.value.ns).toEqual(["dashboard", "common", "auth"]);
  });
});
