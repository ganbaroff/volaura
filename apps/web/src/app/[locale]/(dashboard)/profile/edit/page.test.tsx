import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import type { ButtonHTMLAttributes, ReactNode } from "react";

const mockReplace = vi.fn();
const mockPush = vi.fn();
const mockMutateAsync = vi.fn();
const mockUseProfile = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
  }),
  useParams: () => ({ locale: "en" }),
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: { defaultValue?: string }) => opts?.defaultValue ?? key,
  }),
}));

vi.mock("framer-motion", () => ({
  motion: {
    form: ({ children, ...props }: { children: ReactNode } & Record<string, unknown>) => <form {...props}>{children}</form>,
  },
}));

vi.mock("lucide-react", () => ({
  ChevronLeft: () => null,
  Check: () => null,
}));

vi.mock("@/components/layout/top-bar", () => ({
  TopBar: ({ title }: { title: string }) => <div>{title}</div>,
}));

vi.mock("@/hooks/use-energy-mode", () => ({
  useEnergyMode: () => ({ energy: "full" }),
}));

vi.mock("@/lib/utils/cn", () => ({
  cn: (...parts: Array<string | false | null | undefined>) => parts.filter(Boolean).join(" "),
}));

vi.mock("@/hooks/queries/use-profile", () => ({
  useProfile: () => mockUseProfile(),
  useUpdateProfile: () => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
  }),
}));

import EditProfilePage from "./page";

function makeProfile(overrides: Record<string, unknown> = {}) {
  return {
    id: "user-1",
    username: "atlas",
    display_name: "Atlas",
    bio: "Ops",
    location: "Baku",
    languages: ["English"],
    is_public: false,
    visible_to_orgs: true,
    ...overrides,
  };
}

describe("EditProfilePage safety", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows load error instead of editable form when profile failed to load", () => {
    mockUseProfile.mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error("Profile unavailable"),
    });

    render(<EditProfilePage />);

    expect(screen.getByRole("alert")).toHaveTextContent("Profile unavailable");
    expect(screen.queryByRole("button", { name: "settings.saveChanges" })).not.toBeInTheDocument();
  });

  it("submits persisted booleans from loaded profile state", async () => {
    mockUseProfile.mockReturnValue({
      data: makeProfile(),
      isLoading: false,
      error: null,
    });
    mockMutateAsync.mockResolvedValue(makeProfile());

    render(<EditProfilePage />);

    fireEvent.click(screen.getByRole("button", { name: "settings.saveChanges" }));

    expect(mockMutateAsync).toHaveBeenCalledWith(
      expect.objectContaining({
        is_public: false,
        visible_to_orgs: true,
      }),
    );
  });
});
