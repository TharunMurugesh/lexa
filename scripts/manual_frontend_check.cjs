const { chromium } = require("C:/Users/TM/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/playwright@1.60.0/node_modules/playwright");

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  await page.goto("http://127.0.0.1:5173", { waitUntil: "networkidle" });
  await page.getByRole("button", { name: "Analyze Text" }).click();
  await page.waitForFunction(() => document.querySelectorAll(".dot.done").length === 8, null, { timeout: 20000 });
  await page.locator(".verdict-panel").getByText("Insufficient Evidence").waitFor({ timeout: 5000 });
  await page.screenshot({ path: "manual-check.png", fullPage: true });
  const result = {
    title: await page.locator("h1").innerText(),
    agentsDone: await page.locator(".dot.done").count(),
    verdict: await page.getByText("Insufficient Evidence").first().innerText(),
  };
  console.log(JSON.stringify(result));
  await browser.close();
})();
