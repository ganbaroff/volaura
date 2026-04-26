import { defineConfig } from "vitest/config";

// tg-mini owns its own vitest config — invoked via web's vitest binary
// from pnpm workspace (no devDependency duplication, no lockfile change).
//
// Why this exists: Codex's original test script tried to run web's vitest
// with positional filter args pointing at ../tg-mini/. That failed in CI
// because web's config has `include: ["src/**/*.test.{ts,tsx}"]` (web src
// only), so the filter args matched zero of vitest's collected files →
// "No test files found, exiting with code 1".
//
// Fix: tg-mini supplies its own config so vitest's `--root` + `--config`
// flags steer collection here, with a tg-mini-relative include pattern.
export default defineConfig({
  test: {
    environment: "jsdom",
    globals: true,
    include: ["src/**/*.test.{ts,tsx}"],
    css: false,
  },
});
