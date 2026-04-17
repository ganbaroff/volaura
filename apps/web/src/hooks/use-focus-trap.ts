"use client";

import { useEffect, useRef, type RefObject } from "react";

export function useFocusTrap<T extends HTMLElement>(
  active: boolean
) {
  const ref = useRef<T>(null);
  const previousFocus = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!active || !ref.current) return;

    previousFocus.current = document.activeElement as HTMLElement;

    const container = ref.current;
    const focusable = () =>
      container.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
      );

    const first = focusable()[0];
    first?.focus();

    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") return;
      if (e.key !== "Tab") return;

      const nodes = focusable();
      if (nodes.length === 0) return;

      const firstEl = nodes[0];
      const lastEl = nodes[nodes.length - 1];

      if (e.shiftKey && document.activeElement === firstEl) {
        e.preventDefault();
        lastEl.focus();
      } else if (!e.shiftKey && document.activeElement === lastEl) {
        e.preventDefault();
        firstEl.focus();
      }
    }

    container.addEventListener("keydown", onKeyDown);
    return () => {
      container.removeEventListener("keydown", onKeyDown);
      previousFocus.current?.focus();
    };
  }, [active]);

  return ref;
}
