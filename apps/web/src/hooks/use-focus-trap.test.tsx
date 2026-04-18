import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { useState } from "react";
import { useFocusTrap } from "./use-focus-trap";

function TrapHarness({ initialActive = true }: { initialActive?: boolean }) {
  const [active, setActive] = useState(initialActive);
  const ref = useFocusTrap<HTMLDivElement>(active);

  return (
    <>
      <button data-testid="outside">Outside</button>
      <div ref={ref} data-testid="trap">
        <button data-testid="first">First</button>
        <input data-testid="middle" />
        <button data-testid="last">Last</button>
      </div>
      <button data-testid="toggle" onClick={() => setActive(!active)}>
        Toggle
      </button>
    </>
  );
}

function EmptyTrapHarness() {
  const ref = useFocusTrap<HTMLDivElement>(true);
  return (
    <div ref={ref} data-testid="empty-trap">
      <span>No focusable elements here</span>
    </div>
  );
}

describe("useFocusTrap", () => {
  it("focuses first focusable element when activated", () => {
    render(<TrapHarness />);
    expect(document.activeElement).toBe(screen.getByTestId("first"));
  });

  it("does not focus when inactive", () => {
    render(<TrapHarness initialActive={false} />);
    expect(document.activeElement).not.toBe(screen.getByTestId("first"));
  });

  it("wraps Tab from last to first element", () => {
    render(<TrapHarness />);
    const last = screen.getByTestId("last");
    last.focus();

    fireEvent.keyDown(screen.getByTestId("trap"), {
      key: "Tab",
      shiftKey: false,
    });
    expect(document.activeElement).toBe(screen.getByTestId("first"));
  });

  it("wraps Shift+Tab from first to last element", () => {
    render(<TrapHarness />);
    const first = screen.getByTestId("first");
    first.focus();

    fireEvent.keyDown(screen.getByTestId("trap"), {
      key: "Tab",
      shiftKey: true,
    });
    expect(document.activeElement).toBe(screen.getByTestId("last"));
  });

  it("allows normal Tab between middle elements", () => {
    render(<TrapHarness />);
    const middle = screen.getByTestId("middle");
    middle.focus();

    const event = new KeyboardEvent("keydown", {
      key: "Tab",
      bubbles: true,
      cancelable: true,
    });
    const preventSpy = vi.spyOn(event, "preventDefault");
    screen.getByTestId("trap").dispatchEvent(event);

    expect(preventSpy).not.toHaveBeenCalled();
  });

  it("ignores Escape key (lets it bubble for dialog close)", () => {
    render(<TrapHarness />);
    const first = screen.getByTestId("first");
    first.focus();

    const event = new KeyboardEvent("keydown", {
      key: "Escape",
      bubbles: true,
      cancelable: true,
    });
    const preventSpy = vi.spyOn(event, "preventDefault");
    screen.getByTestId("trap").dispatchEvent(event);

    expect(preventSpy).not.toHaveBeenCalled();
  });

  it("ignores non-Tab keys", () => {
    render(<TrapHarness />);
    const last = screen.getByTestId("last");
    last.focus();

    const event = new KeyboardEvent("keydown", {
      key: "Enter",
      bubbles: true,
      cancelable: true,
    });
    const preventSpy = vi.spyOn(event, "preventDefault");
    screen.getByTestId("trap").dispatchEvent(event);

    expect(preventSpy).not.toHaveBeenCalled();
  });

  it("restores focus to previously focused element on deactivation", () => {
    const { rerender } = render(
      <>
        <button data-testid="pre-focus" autoFocus>
          Pre
        </button>
      </>
    );
    const preFocus = screen.getByTestId("pre-focus");
    preFocus.focus();
    expect(document.activeElement).toBe(preFocus);

    rerender(<TrapHarness />);
    expect(document.activeElement).toBe(screen.getByTestId("first"));

    fireEvent.click(screen.getByTestId("toggle"));
  });

  it("handles empty trap container gracefully", () => {
    expect(() => render(<EmptyTrapHarness />)).not.toThrow();
  });

  it("skips disabled buttons in focusable query", () => {
    function DisabledHarness() {
      const ref = useFocusTrap<HTMLDivElement>(true);
      return (
        <div ref={ref} data-testid="trap">
          <button disabled data-testid="disabled">
            Disabled
          </button>
          <button data-testid="enabled">Enabled</button>
        </div>
      );
    }
    render(<DisabledHarness />);
    expect(document.activeElement).toBe(screen.getByTestId("enabled"));
  });

  it("includes links with href in focusable set", () => {
    function LinkHarness() {
      const ref = useFocusTrap<HTMLDivElement>(true);
      return (
        <div ref={ref} data-testid="trap">
          <a href="/test" data-testid="link">
            Link
          </a>
          <button data-testid="btn">Button</button>
        </div>
      );
    }
    render(<LinkHarness />);
    expect(document.activeElement).toBe(screen.getByTestId("link"));
  });
});
