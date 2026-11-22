import { expect, test, type Page } from "@playwright/test";

const nav = (page: Page, name: string) => page.locator("nav").getByRole("link", { name, exact: true });

const adminPassword = process.env.ADMIN_PASSWORD;
if (!adminPassword) throw new Error("ADMIN_PASSWORD is not set: export it or define it in the root .env");
const CREDENTIALS = { username: "admin", password: adminPassword };

async function login(page: Page) {
  await page.goto("/");
  await page.getByRole("textbox").first().fill(CREDENTIALS.username);
  await page.locator('input[type="password"]').fill(CREDENTIALS.password);
  await page.locator("form").getByRole("button").click();
  await expect(nav(page, "Findingi")).toBeVisible();
}

const consoleProblems: string[] = [];

test.beforeEach(({ page }) => {
  consoleProblems.length = 0;
  page.on("console", (message) => {
    if (["error", "warning"].includes(message.type())) consoleProblems.push(message.text());
  });
});

// Playwright requires the fixtures argument to be a destructuring pattern.
// eslint-disable-next-line no-empty-pattern
test.afterEach(({}, testInfo) => {
  // A wrong password is answered with 401, which the browser logs by design.
  if (!testInfo.title.includes("rejects")) expect(consoleProblems).toEqual([]);
});

test("login rejects a wrong password and accepts the right one", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("textbox").first().fill(CREDENTIALS.username);
  await page.locator('input[type="password"]').fill("wrong");
  await page.locator("form").getByRole("button").click();
  await expect(nav(page, "Findingi")).toHaveCount(0);
  await login(page);
});

test("scan of a demo page streams pipeline stages and ends with a result", async ({ page }) => {
  await login(page);
  await nav(page, "Skanuj URL").click();
  await page.getByRole("textbox").first().fill("http://demo-sites:8080/landing-aurum-cfd");
  await page.getByRole("button", { name: /skanuj/i }).click();
  await expect(page.getByRole("status").filter({ hasText: /Utworzono findingi|już skanowana|Brak findingów/ })).toBeVisible({ timeout: 90_000 });
});

test("finding detail shows criteria, evidence integrity and the screenshot", async ({ page }) => {
  await login(page);
  await nav(page, "Findingi").click();
  await page.getByPlaceholder(/Szukaj/).fill("Aurum Capital - CFD");
  await page.locator(`main a[href^="/findings/"]`).first().click();
  await expect(page.getByRole("heading", { name: /Kryteria zgodności/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Łańcuch dowodowy" })).toBeVisible();
  await expect(page.getByAltText("Zrzut ekranu zapisany jako dowód")).toBeVisible();
});

test("findings filters and sorting survive opening a finding and going back", async ({ page }) => {
  await login(page);
  await nav(page, "Findingi").click();
  const sort = page.getByLabel("Sortowanie");
  const webSource = page.locator(".check").filter({ has: page.locator(".check__label", { hasText: /^web$/ }) }).locator("input");
  await sort.selectOption("date_asc");
  await webSource.click();
  await expect(webSource).toBeChecked();

  await page.locator(`main a[href^="/findings/"]`).first().click();
  await page.getByRole("link", { name: /← Findingi/ }).click();
  await expect(sort).toHaveValue("date_asc");
  await expect(webSource).toBeChecked();

  await page.locator(`main a[href^="/findings/"]`).first().click();
  await page.goBack();
  await expect(sort).toHaveValue("date_asc");
  await expect(webSource).toBeChecked();
});

test("an analyst decision changes the finding status", async ({ page }) => {
  await login(page);
  await nav(page, "Findingi").click();
  await page.locator(`main a[href^="/findings/"]`).first().click();
  await page.locator("button:not([disabled])", { hasText: /^(Przejmij|Potwierdź|Odrzuć)$/ }).first().click();
  await expect(page.getByRole("status")).toBeVisible();
});

test("calibration shows the active-learning queue", async ({ page }) => {
  await login(page);
  await nav(page, "Kalibracja").click();
  await expect(page.getByRole("heading", { name: "Do oceny w pierwszej kolejności" })).toBeVisible();
});

test("campaigns page groups near-identical content across authors", async ({ page }) => {
  await login(page);
  await nav(page, "Kampanie").click();
  await expect(page.getByRole("heading", { name: "Kampanie" })).toBeVisible();
  await expect(page.getByText("Wspólne kody promo")).toBeVisible();
});

test("calibration shows the confusion matrix and model versions", async ({ page }) => {
  await login(page);
  await nav(page, "Kalibracja").click();
  await expect(page.getByRole("heading", { name: /Jakość modelu/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Wersje modelu" })).toBeVisible();
});

test("settings page lists sources and the registry summary", async ({ page }) => {
  await login(page);
  await nav(page, "Ustawienia").click();
  await expect(page.getByRole("heading", { name: "Źródła danych" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Rejestr podmiotów" })).toBeVisible();
});

test("system health shows live service status", async ({ page }) => {
  await login(page);
  await nav(page, "Zdrowie systemu").click();
  await expect(page.getByRole("heading", { name: "Usługi" })).toBeVisible();
  await expect(page.getByText("postgres")).toBeVisible();
});
