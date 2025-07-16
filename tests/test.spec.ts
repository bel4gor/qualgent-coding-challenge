import { test, expect } from "appwright";

test("Open Playwright on Wikipedia and verify Microsoft is visible", async ({ device }) => {
  await device.getByText("Skip").tap();
  const searchInput = device.getByText("Search Wikipedia", { exact: true });
  await searchInput.tap();
  await searchInput.fill("playwright");
  await device.getByText("Playwright (software)").tap();
  await expect(device.getByText("Microsoft")).toBeVisible();
});
