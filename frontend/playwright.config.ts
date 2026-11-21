import { existsSync } from "node:fs";
import { defineConfig } from "@playwright/test";

const rootEnv = new URL("../.env", import.meta.url);
if (existsSync(rootEnv)) process.loadEnvFile(rootEnv);

export default defineConfig({
  testDir: "e2e",
  timeout: 60_000,
  retries: 0,
  reporter: "list",
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:47173",
    channel: process.env.E2E_BROWSER_CHANNEL ?? undefined,
  },
});
