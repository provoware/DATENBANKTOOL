import { spawnSync } from "node:child_process";

const mode = process.argv[2] === "--write" ? "--write" : "--check";
const targets = [
  "src/web/**/*.{html,js,css,json}",
  "src/config/**/*.json",
  "MANIFEST.json",
  "VERSION.json",
  "TOOL_SCHEMA.json",
  "tests/browser/**/*.js",
  "playwright.config.js",
];

const command = process.platform === "win32" ? "npx.cmd" : "npx";
const result = spawnSync(command, ["prettier", mode, ...targets], {
  stdio: "inherit",
  shell: false,
});

process.exit(result.status ?? 1);
