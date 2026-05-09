import { expect, test } from "@playwright/test";

test("Phase 3 happy path: login, scan, quality, glossary, lineage, policies, catalogue, settings", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL("/login");
  await page.getByLabel("Email").fill("admin@datagov.local");
  await page.getByLabel("Password").fill("admin123");
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(page).toHaveURL("/");
  await expect(page.getByText("Backend API")).toBeVisible();

  await page.getByRole("link", { name: "Run scan" }).click();
  await expect(page.getByRole("heading", { name: "Run scan" })).toBeVisible();
  await expect(page.getByText("Sample Business SQLite")).toBeVisible();
  await page.getByRole("button", { name: "Continue" }).click();
  page.once("dialog", async (dialog) => {
    expect(dialog.message()).toContain("Save this scheduled scan");
    await dialog.accept();
  });
  await page.getByRole("button", { name: "Save schedule" }).click();
  await expect(page.getByText("Scheduled scan saved")).toBeVisible();
  page.once("dialog", async (dialog) => {
    expect(dialog.message()).toContain("Start scan");
    await dialog.accept();
  });
  await page.getByRole("button", { name: "Start scan" }).click();
  await expect(page.getByText(/^Scan complete\./)).toBeVisible();
  await expect(page.getByText("Assets scanned")).toBeVisible();
  await expect(page.getByText("Policies applied")).toBeVisible();

  await page.getByRole("link", { name: "Quality" }).click();
  await expect(page.getByRole("heading", { name: "Quality" })).toBeVisible();
  await expect(page.getByText("Average score")).toBeVisible();
  await page.goto("/quality/issues");
  await expect(page.getByRole("heading", { name: "Quality issues" })).toBeVisible();
  await expect(page.getByRole("table")).toBeVisible();

  await page.getByRole("link", { name: "Glossary" }).click();
  await expect(page.getByRole("heading", { name: "Glossary" })).toBeVisible();
  await expect(page.getByRole("cell", { name: "Customer", exact: true })).toBeVisible();
  const termName = `E2E Term ${Date.now()}`;
  await page.getByLabel("Term").fill(termName);
  await page.getByLabel("Definition").fill("A test business term created by the E2E journey.");
  await page.getByLabel("Synonyms").fill("e2e");
  page.once("dialog", async (dialog) => {
    expect(dialog.message()).toContain("Create this glossary term");
    await dialog.accept();
  });
  await page.getByRole("button", { name: "Create term" }).click();
  await expect(page.getByText("Glossary term created").first()).toBeVisible();
  await expect(page.getByText(termName)).toBeVisible();

  await page.getByRole("link", { name: "Lineage" }).click();
  await expect(page.getByRole("heading", { name: "Lineage" })).toBeVisible();
  page.once("dialog", async (dialog) => {
    expect(dialog.message()).toContain("Extract table-level lineage");
    await dialog.accept();
  });
  await page.getByRole("button", { name: "Extract lineage" }).click();
  await expect(page.getByText("Lineage extracted").first()).toBeVisible();
  await expect(page.getByRole("cell", { name: "customers" }).first()).toBeVisible();
  await expect(page.getByRole("cell", { name: "orders" }).first()).toBeVisible();

  await page.getByRole("link", { name: "Policies" }).click();
  await expect(page.getByRole("heading", { name: "Policies" })).toBeVisible();
  const classificationName = `Highly Confidential ${Date.now()}`;
  await page.getByLabel("Classification name").fill(classificationName);
  await page.getByLabel("Description").fill("E2E custom classification that masks sample data.");
  await page.getByLabel("Color").selectOption("danger");
  await page.getByLabel("Mask samples").check();
  page.once("dialog", async (dialog) => {
    expect(dialog.message()).toContain("Create classification");
    await dialog.accept();
  });
  await page.getByRole("button", { name: "Create classification" }).click();
  await expect(page.getByText("Classification created").first()).toBeVisible();
  await expect(page.getByText(classificationName).first()).toBeVisible();
  const policyName = `E2E email policy ${Date.now()}`;
  await page.getByLabel("Policy name").fill(policyName);
  await page.getByLabel("Column contains").fill("email");
  await page.getByLabel("Policy classification").selectOption(classificationName);
  page.once("dialog", async (dialog) => {
    expect(dialog.message()).toContain("Create this active classification policy");
    await dialog.accept();
  });
  await page.getByRole("button", { name: "Create policy" }).click();
  await expect(page.getByText("Policy created").first()).toBeVisible();
  await expect(page.getByText(policyName)).toBeVisible();

  await page.getByRole("link", { name: "Catalogue" }).click();
  await expect(page.getByRole("heading", { name: "Catalogue" })).toBeVisible();
  await expect(page.getByRole("table")).toBeVisible();
  await page.getByRole("link", { name: "customers" }).first().click();
  await expect(page.getByPlaceholder("Add column description").first()).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "Sample data" })).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "Standard format" })).toBeVisible();
  await expect(page.locator('td span[title="*****"]').first()).toBeVisible();
  page.once("dialog", async (dialog) => {
    expect(dialog.message()).toContain("Detect standard formats");
    await dialog.accept();
  });
  await page.getByRole("button", { name: "Detect formats" }).click();
  await expect(page.getByText("Detected standard formats")).toBeVisible();
  await expect(page.getByLabel("Standard format for email")).toHaveValue("valid email address");
  await page.getByLabel("Standard format for id").fill("integer identifier");
  await page.getByRole("button", { name: "Save", exact: true }).first().click();
  await expect(page.getByText("Column metadata saved").first()).toBeVisible();
  page.once("dialog", async (dialog) => {
    expect(dialog.message()).toContain("Generate AI metadata");
    await dialog.accept();
  });
  await page.getByRole("button", { name: "Generate metadata" }).click();
  await expect(page.getByText(/Generated metadata with/)).toBeVisible();
  await expect(page.getByPlaceholder("Add column description").first()).not.toHaveValue("");
  await page.getByRole("button", { name: "Preview sample" }).click();
  await expect(page.getByText("Sample loaded")).toBeVisible();

  await page.getByRole("link", { name: "Settings" }).click();
  await expect(page.getByRole("heading", { name: "Connectors" })).toBeVisible();
  await expect(page.getByText("Sample Business SQLite")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Notifications" })).toBeVisible();
  const notificationTarget = `e2e-${Date.now()}@datagov.local`;
  await page.getByLabel("Channel").selectOption("email");
  await page.getByLabel("Target").fill(notificationTarget);
  await page.getByRole("button", { name: "Add notification" }).click();
  await expect(page.getByText("Notification setting created")).toBeVisible();
  await expect(page.getByRole("cell", { name: notificationTarget })).toBeVisible();
  await page
    .locator("tr")
    .filter({ has: page.getByRole("cell", { name: notificationTarget }) })
    .getByRole("button", { name: "Test" })
    .click();
  await expect(page.getByText("Localhost notification test recorded in audit log")).toBeVisible();
  await page
    .locator("tr")
    .filter({ has: page.getByRole("cell", { name: notificationTarget }) })
    .getByRole("button", { name: "Delete" })
    .click();
  await expect(page.getByRole("cell", { name: notificationTarget })).toHaveCount(0);

  await page.goto("/settings/users");
  await expect(page.getByRole("heading", { name: "Users and roles" })).toBeVisible();
  await expect(page.getByText("admin@datagov.local")).toBeVisible();
});
