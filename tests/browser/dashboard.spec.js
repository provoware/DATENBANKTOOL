import { expect, test } from "@playwright/test";

async function collectConsoleErrors(page) {
  const errors = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  page.on("pageerror", (error) => errors.push(error.message));
  return errors;
}

test("Dashboard lädt Metadaten, Status und Kernkarten ohne JS-Fehler", async ({ page }, testInfo) => {
  const errors = await collectConsoleErrors(page);
  await page.goto("/");

  const metaResponse = await page.request.get("/api/project/meta");
  expect(metaResponse.ok()).toBeTruthy();
  const meta = await metaResponse.json();

  await expect(page.locator("#liveStatus")).not.toContainText("STATUS WIRD GELADEN");
  await expect(page.locator("#progressValue")).toHaveText(`${meta.product.progress_percent} %`);
  await expect(page.locator("#footerText")).toContainText(meta.product.version);
  await expect(page.locator(".grid .card")).toHaveCount(6);
  await expect(page.locator("#main")).toBeVisible();

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(1);
  expect(errors).toEqual([]);

  await testInfo.attach("dashboard", {
    body: await page.screenshot({ fullPage: true }),
    contentType: "image/png",
  });
});

test("Kurzhilfe ist per Tastatur erreichbar und setzt den Fokus", async ({ page }) => {
  await page.goto("/");
  const button = page.locator("#helpButton");
  const panel = page.locator("#helpPanel");

  await button.focus();
  await expect(button).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(panel).toBeVisible();
  await expect(panel).toBeFocused();
  await expect(button).toContainText(/hilfe/i);
});

test("Skip-Link führt per Tastatur zum Hauptinhalt", async ({ page }) => {
  await page.goto("/");
  await page.keyboard.press("Tab");
  const skip = page.locator(".skip-link");
  await expect(skip).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#main")).toBeFocused();
});
