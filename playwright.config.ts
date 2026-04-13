import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 60_000,
  retries: 1,
  use: {
    baseURL:
      process.env.VOLAURA_URL || "https://volaura.app",
    extraHTTPHeaders: {
      Accept: "application/json",
    },
  },
  reporter: [["html", { open: "never" }], ["list"]],
});
