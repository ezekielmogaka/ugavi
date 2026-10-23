import { expect, test } from '@playwright/test';

test('health endpoint and administrator desk load', async ({ page }) => {
  const ping = await page.request.get('/api/method/frappe.ping');
  expect(ping.ok()).toBeTruthy();

  await page.goto('/login');
  await page.locator('#login_email').fill('Administrator');
  await page.locator('#login_password').fill('admin');
  await page.getByRole('button', { name: 'Continue' }).click();
  await expect(page).toHaveURL(/\/(app|desk)/);

  await page.goto('/app/purchase-requisition');
  await expect(page.locator('body')).toContainText('Purchase Requisition');

  await page.goto('/app/tender');
  await expect(page.locator('body')).toContainText('Tender');
});

test('supplier portal requires an authenticated supplier identity', async ({ page }) => {
  await page.goto('/supplier/dashboard');
  await expect(page.getByRole('heading', { name: 'Supplier Portal' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Sign in securely' })).toBeVisible();
  await expect(page.locator('.ugavi-portal__hero')).toBeVisible();

  const brand = await page.locator('.ugavi-portal').evaluate((element) =>
    getComputedStyle(element).getPropertyValue('--ugavi-brand').trim()
  );
  expect(brand).toBe('#2e3194');
});

test('seeded LOKADO supplier sees an identity-scoped dashboard', async ({ page }) => {
  await page.goto('/login');
  await page.locator('#login_email').fill('lodwar-supplies@outlook.com');
  await page.locator('#login_password').fill('Ugavi@2024');
  await Promise.all([
    page.waitForURL(/\/supplier\/dashboard/),
    page.getByRole('button', { name: 'Continue' }).click(),
  ]);

  await expect(page.getByRole('heading', { name: 'Lodwar General Supplies' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Open tenders' })).toBeVisible();
  for (const heading of [
    'Supplier profile',
    'Prequalification',
    'Submit a bid',
    'Clarifications',
    'Tender complaints',
    'Awards',
    'Contracts',
    'Orders and deliveries',
    'Supplier invoices',
    'Supplier evaluations',
    'Notifications',
  ]) {
    await expect(page.getByRole('heading', { name: heading })).toBeVisible();
  }
  await expect(page.getByRole('heading', { name: /% complete/ })).toBeVisible();
  await expect(page.getByRole('progressbar', { name: 'Supplier journey completion' })).toBeVisible();

  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator('.ugavi-portal__metrics')).toHaveCSS(
    'grid-template-columns',
    /^\d+(\.\d+)?px$/
  );
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= 390)).toBeTruthy();
});
