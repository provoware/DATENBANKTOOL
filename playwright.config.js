import { defineConfig } from "@playwright/test";

const channel = process.env.PW_CHANNEL || undefined;

export default defineConfig({
  testDir: "./tests/browser",
  timeout: 30000,
  expect: { timeout: 5000 },
  reporter: [["list"], ["html", { outputFolder: "playwright-report", open: "never" }]],
  use: {
    baseURL: "http://127.0.0.1:8765",
    channel,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    video: "retain-on-failure",
  },
  webServer: {
    command: "python3 -m src.server",
    url: "http://127.0.0.1:8765/api/health",
    reuseExistingServer: !process.env.CI,
    timeout: 20000,
  },
  projects: [
    {
      name: "compact-800x600",
      use: { viewport: { width: 800, height: 600 } },
    },
    {
      // Approximates the reduced CSS viewport at 800x600 and 200% browser zoom.
      name: "compact-200-percent-equivalent",
      use: { viewport: { width: 400, height: 300 } },
    },
    {
      name: "desktop-1366x768",
      use: { viewport: { width: 1366, height: 768 } },
    },
    {
      name: "desktop-1600x900",
      use: { viewport: { width: 1600, height: 900 } },
    },
    {
      name: "desktop-1920x1080",
      use: { viewport: { width: 1920, height: 1080 } },
    },
  ],
});
