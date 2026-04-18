import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, act, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";

// ── Mocks ─────────────────────────────────────────────────────────────────────

// framer-motion: skip animation, render children directly
const MotionDiv = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement> & { children?: React.ReactNode }>(
  ({ children, ...rest }, ref) => React.createElement("div", { ...rest, ref }, children)
);
MotionDiv.displayName = "MotionDiv";

function AnimatePresenceMock({ children }: { children: React.ReactNode }) {
  return React.createElement(React.Fragment, null, children);
}

vi.mock("framer-motion", () => ({
  motion: {
    div: MotionDiv,
  },
  AnimatePresence: AnimatePresenceMock,
}));

// ── Import after mocks ────────────────────────────────────────────────────────

import { Toaster, toast, dismissToast } from "@/components/ui/toast";

// ── Helpers ───────────────────────────────────────────────────────────────────

// The toast store is module-level. Always render <Toaster /> FIRST so it
// subscribes, THEN call toast() so the state update is received.

function renderToaster() {
  return render(<Toaster />);
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("Toaster — region container", () => {
  it("renders a region landmark", () => {
    renderToaster();
    expect(screen.getByRole("region")).toBeInTheDocument();
  });

  it("region has accessible aria-label for notifications", () => {
    renderToaster();
    expect(screen.getByRole("region")).toHaveAttribute("aria-label", "Notifications");
  });

  it("renders no toast items when empty", () => {
    renderToaster();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});

describe("Toaster — showing toasts", () => {
  let toastIds: string[] = [];

  afterEach(() => {
    act(() => {
      toastIds.forEach((id) => dismissToast(id));
    });
    toastIds = [];
  });

  it("renders a toast message when toast() is called", () => {
    renderToaster();
    act(() => {
      toastIds.push(toast("Hello world"));
    });
    expect(screen.getByText("Hello world")).toBeInTheDocument();
  });

  it("rendered toast item has role alert", () => {
    renderToaster();
    act(() => {
      toastIds.push(toast("Alert message"));
    });
    expect(screen.getAllByRole("alert").length).toBeGreaterThan(0);
  });

  it("renders multiple toasts simultaneously", () => {
    renderToaster();
    act(() => {
      toastIds.push(toast("First toast"));
      toastIds.push(toast("Second toast"));
    });
    expect(screen.getByText("First toast")).toBeInTheDocument();
    expect(screen.getByText("Second toast")).toBeInTheDocument();
  });

  it("toast function returns an id string", () => {
    renderToaster();
    let id: string = "";
    act(() => {
      id = toast("Test");
      toastIds.push(id);
    });
    expect(typeof id).toBe("string");
    expect(id.length).toBeGreaterThan(0);
  });
});

describe("Toaster — toast types", () => {
  let toastIds: string[] = [];

  afterEach(() => {
    act(() => {
      toastIds.forEach((id) => dismissToast(id));
    });
    toastIds = [];
  });

  it("defaults to info type when no type passed — shows info icon", () => {
    renderToaster();
    act(() => {
      toastIds.push(toast("Info message"));
    });
    expect(screen.getByText("ℹ️")).toBeInTheDocument();
  });

  it("renders success type with check icon", () => {
    renderToaster();
    act(() => {
      toastIds.push(toast("Done!", "success"));
    });
    expect(screen.getByText("✓")).toBeInTheDocument();
  });

  it("renders warning type with warning icon", () => {
    renderToaster();
    act(() => {
      toastIds.push(toast("Be careful", "warning"));
    });
    expect(screen.getByText("⚠")).toBeInTheDocument();
  });

  it("renders error type with exclamation icon", () => {
    renderToaster();
    act(() => {
      toastIds.push(toast("Something failed", "error"));
    });
    expect(screen.getByText("!")).toBeInTheDocument();
  });

  it("error toast has aria-live assertive", () => {
    renderToaster();
    act(() => {
      toastIds.push(toast("Critical error", "error"));
    });
    const alerts = screen.getAllByRole("alert");
    const errorAlert = alerts.find((el) => el.getAttribute("aria-live") === "assertive");
    expect(errorAlert).toBeTruthy();
  });

  it("non-error toasts have aria-live polite", () => {
    renderToaster();
    act(() => {
      toastIds.push(toast("Info toast", "info"));
    });
    const alerts = screen.getAllByRole("alert");
    const politeAlert = alerts.find((el) => el.getAttribute("aria-live") === "polite");
    expect(politeAlert).toBeTruthy();
  });
});

describe("Toaster — dismiss button", () => {
  let toastIds: string[] = [];

  afterEach(() => {
    act(() => {
      toastIds.forEach((id) => dismissToast(id));
    });
    toastIds = [];
  });

  it("renders a dismiss button on each toast", () => {
    renderToaster();
    act(() => {
      toastIds.push(toast("Dismissible"));
    });
    expect(screen.getByRole("button", { name: "Dismiss" })).toBeInTheDocument();
  });

  it("clicking dismiss button removes the toast", async () => {
    const user = userEvent.setup();
    renderToaster();
    act(() => {
      toastIds.push(toast("Remove me"));
    });
    expect(screen.getByText("Remove me")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Dismiss" }));
    await waitFor(() => {
      expect(screen.queryByText("Remove me")).not.toBeInTheDocument();
    });
    toastIds = []; // already dismissed
  });
});

describe("Toaster — dismissToast API", () => {
  let toastIds: string[] = [];

  afterEach(() => {
    act(() => {
      toastIds.forEach((id) => dismissToast(id));
    });
    toastIds = [];
  });

  it("dismissToast removes toast by id", () => {
    renderToaster();
    let id: string = "";
    act(() => {
      id = toast("Will be dismissed");
      toastIds.push(id);
    });
    expect(screen.getByText("Will be dismissed")).toBeInTheDocument();

    act(() => {
      dismissToast(id);
      toastIds = toastIds.filter((t) => t !== id);
    });

    expect(screen.queryByText("Will be dismissed")).not.toBeInTheDocument();
  });

  it("dismissToast with unknown id does not crash", () => {
    renderToaster();
    expect(() => {
      act(() => {
        dismissToast("nonexistent-id-xyz");
      });
    }).not.toThrow();
  });
});

describe("Toaster — auto-dismiss", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("info toast auto-dismisses after 5 seconds", () => {
    renderToaster();
    act(() => {
      toast("Auto dismiss me", "info");
    });
    expect(screen.getByText("Auto dismiss me")).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(5001);
    });

    expect(screen.queryByText("Auto dismiss me")).not.toBeInTheDocument();
  });

  it("success toast auto-dismisses after 5 seconds", () => {
    renderToaster();
    act(() => {
      toast("Saved!", "success");
    });
    expect(screen.getByText("Saved!")).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(5001);
    });

    expect(screen.queryByText("Saved!")).not.toBeInTheDocument();
  });

  it("error toast does NOT auto-dismiss after 5 seconds", () => {
    renderToaster();
    let id: string = "";
    act(() => {
      id = toast("Persistent error", "error");
    });

    act(() => {
      vi.advanceTimersByTime(5001);
    });

    expect(screen.getByText("Persistent error")).toBeInTheDocument();

    // Cleanup
    act(() => {
      dismissToast(id);
    });
  });
});
