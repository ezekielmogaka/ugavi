import { expect, test } from '@playwright/test';

for (const [email, doctypes] of [
  ['programme@lokado.org', ['Purchase Requisition']],
  ['approver1@lokado.org', ['Purchase Requisition']],
  ['approver2@lokado.org', ['Purchase Requisition']],
  ['procurement@lokado.org', ['Tender', 'Supplier Prequalification', 'Ugavi Contract', 'Ugavi Supplier Evaluation']],
  ['opening1@lokado.org', ['Tender', 'Bid Opening Record']],
  ['opening2@lokado.org', ['Tender', 'Bid Opening Record']],
  ['opening3@lokado.org', ['Tender', 'Bid Opening Record']],
  ['committee@lokado.org', ['Bid Evaluation Summary']],
  ['storekeeper@lokado.org', ['Purchase Receipt']],
  ['logistics@lokado.org', ['Donor Warehouse', 'Monthly Stock Report', 'Inter Donor Transfer', 'Stock Entry']],
  ['fleet@lokado.org', ['Vehicle', 'Vehicle Allocation', 'Fuel Log', 'Spare Parts Issue', 'Fleet Utilization Report']],
  ['assets@lokado.org', ['Asset Register', 'Ugavi Asset Movement', 'Asset Verification', 'Asset Disposal']],
  ['finance@lokado.org', ['Three Way Match', 'Purchase Invoice', 'Payment Entry', 'Budget', 'Landed Cost Voucher']],
  ['auditor@lokado.org', ['Audit Log', 'Delegation of Authority', 'Segregation of Duties']],
] as const) {
  test(`${email} can access the documented demo records`, async ({ page }) => {
    await page.goto('/login');
    await page.locator('#login_email').fill(email);
    await page.locator('#login_password').fill('Ugavi@2024');
    await page.getByRole('button', { name: 'Continue' }).click();
    await expect(page).toHaveURL(/\/(app|desk)/);

    for (const doctype of doctypes) {
      const response = await page.request.get('/api/method/frappe.client.get_list', {
        params: { doctype, fields: '["name"]', limit_page_length: 1 },
      });
      expect(response.ok(), `${email}: read ${doctype}`).toBeTruthy();
      const { message } = await response.json();
      expect(Array.isArray(message), `${doctype}: list response`).toBeTruthy();
      // These records only exist after the real opening/evaluation workflow.
      if (!['Bid Opening Record', 'Bid Evaluation Summary'].includes(doctype)) {
        expect(message.length, `${email}: seeded ${doctype} evidence`).toBeGreaterThan(0);
      }
    }

    const route = doctypes[0].toLowerCase().replaceAll(' ', '-');
    await page.goto(`/app/${route}`);
    await expect(page.locator('.page-title:visible').first()).toContainText(doctypes[0]);
  });
}

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
