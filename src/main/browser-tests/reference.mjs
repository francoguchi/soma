// Actual encrypted Reference host. Synthetic operator data; no API mocks.
import assert from 'node:assert/strict';
import {chromium, expect} from '@playwright/test';
const origin = process.argv[2];
assert.match(origin, /^http:\/\/127\.0\.0\.1:[1-9][0-9]*$/u);
const browser = await chromium.launch({headless: true, channel: 'chrome'});
const context = await browser.newContext({viewport: {width: 1440, height: 1000}});
const page = await context.newPage();
const errors = [];
let sessionContext = null;
page.on('response', async response => {
  if (new URL(response.url()).pathname === '/api/v1/bootstrap' && response.ok()) {
    const value = await response.json();
    if (value.csrf_token) sessionContext = {run_id: value.run_id, csrf_token: value.csrf_token};
  }
});
page.on('pageerror', error => errors.push(error.message));
page.on('request', request => assert.equal(new URL(request.url()).origin, origin));
async function enter(path) {await page.goto(origin + path); await expect(page.getByRole('heading', {name: /Settings/}).first()).toBeVisible();}
async function create(kind, name, extra = null) {
  await enter('/settings/reference-data/' + kind + '/new');
  await page.getByLabel('Name', {exact: true}).fill(name);
  if (extra) await extra();
  await page.getByRole('button', {name: 'Create reference explicitly', exact: true}).click();
  await expect(page).toHaveURL(new RegExp('/settings/reference-data/' + kind + '/[0-9a-f-]{36}$'));
  await expect(page.getByLabel('Name', {exact: true})).toHaveValue(name);
  return page.url().split('/').at(-1);
}
async function nativeApi(path, body, method = 'POST') {
  return page.evaluate(async ({path, body, method, boot}) => {
    const result = await fetch('/api/v1' + path, {method, headers: {'Content-Type': 'application/json', 'X-SOMA-Run': boot.run_id, 'X-SOMA-CSRF': boot.csrf_token}, ...(body === undefined ? {} : {body: JSON.stringify(body)})});
    return {status: result.status, value: await result.json()};
  }, {path, body, method, boot: sessionContext});
}
try {
  await page.goto(origin + '/settings/reference-data/customer_organization/new');
  await page.getByLabel('Password', {exact: true}).fill('Synthetic Reference UI password 42');
  await page.getByLabel('Confirm password').fill('Synthetic Reference UI password 42');
  await page.getByRole('button', {name: 'Create password and sign in'}).click();
  await expect(page.getByRole('heading', {name: 'Settings / Reference data'})).toBeVisible();
  assert.equal(await page.getByRole('group', {name: 'Workspaces', exact: true}).getByRole('button').count(), 6);
  await expect(page.getByRole('group', {name: 'Workspaces', exact: true}).getByRole('button', {name: 'Settings', exact: true})).toBeEnabled();
  assert.equal(await page.getByRole('group', {name: 'Workspaces', exact: true}).getByRole('button', {name: 'Customers', exact: true}).count(), 0);
  const first = await create('customer_organization', 'Customer One', async () => page.getByLabel('Initial Account Code (optional)').fill('UI-CODE'));
  const second = await create('customer_organization', 'Customer Two');
  await page.getByLabel('Account Code', {exact: true}).fill('UI-CODE');
  await page.getByRole('button', {name: 'Set Account Code', exact: true}).click();
  await expect(page.getByRole('alert').filter({hasText: 'ACCOUNT_CODE_CONFLICT_REVIEW'}).first()).toBeVisible();
  await expect(page.getByLabel('Account Code', {exact: true})).toHaveValue('UI-CODE');
  await page.getByLabel('Account Code reason category').fill('operator_review');
  await page.getByRole('button', {name: 'Load Account Code review'}).click();
  await expect(page.getByText('Exact claimant count: 1')).toBeVisible();
  const race = await nativeApi('/reference/customer-organizations', {command_id: crypto.randomUUID(), name: 'Concurrent unrelated Customer'});
  assert.equal(race.status, 200);
  await page.getByRole('button', {name: 'Confirm reviewed Account Code action…'}).click();
  await page.getByRole('button', {name: 'Submit exact reviewed action'}).click();
  await expect(page.getByRole('alert').filter({hasText: 'REVIEW_CONTEXT_STALE'}).first()).toBeVisible();
  assert.equal(await page.getByRole('button', {name: 'Submit exact reviewed action'}).count(), 0);
  await page.getByRole('button', {name: 'Load Account Code review'}).click();
  await expect(page.getByText('Exact claimant count: 1')).toBeVisible();
  await page.getByRole('button', {name: 'Confirm reviewed Account Code action…'}).click();
  await page.getByRole('button', {name: 'Submit exact reviewed action'}).click();
  await expect(page.getByText('Current: UI-CODE.', {exact: false})).toBeVisible();
  await page.getByLabel('Match Account Code').fill('UI-CODE');
  await page.getByRole('button', {name: 'Find candidates'}).click();
  await expect(page.getByRole('status').filter({hasText: 'AMBIGUOUS · 2 exact candidates'})).toBeVisible();
  await page.getByLabel('Name', {exact: true}).fill('Unsaved Customer intent');
  await page.getByRole('button', {name: 'Profile', exact: true}).click();
  await expect(page.getByRole('dialog', {name: 'Leave unsaved changes?'})).toBeVisible();
  await page.getByRole('dialog').getByRole('button', {name: 'Cancel', exact: true}).click();
  await expect(page.getByLabel('Name', {exact: true})).toHaveValue('Unsaved Customer intent');
  await expect(page.getByRole('status').filter({hasText: 'Recovery: checkpointed'})).toBeVisible({timeout: 15000});
  await page.reload();
  await page.getByRole('button', {name: 'Restore intent', exact: true}).click();
  await expect(page.getByLabel('Name', {exact: true})).toHaveValue('Unsaved Customer intent');
  const foreign = await nativeApi('/reference/customer-organizations/' + second, {command_id: crypto.randomUUID(), base_revision: 2, name: 'Concurrent Customer name'}, 'PATCH');
  assert.equal(foreign.status, 200);
  await page.getByRole('button', {name: 'Save name', exact: true}).click();
  await expect(page.getByRole('alert').filter({hasText: 'STALE_REVISION'}).first()).toBeVisible();
  await expect(page.getByLabel('Name', {exact: true})).toHaveValue('Unsaved Customer intent');
  await page.getByRole('button', {name: 'Refresh current state'}).click();
  await expect(page.getByText('Concurrent Customer name', {exact: true}).first()).toBeVisible();
  await expect(page.getByRole('button', {name: 'Save name', exact: true})).toBeDisabled();
  await page.getByRole('button', {name: 'Use reviewed intent against current revision'}).click();
  await expect(page.getByRole('button', {name: 'Save name', exact: true})).toBeEnabled();
  await expect(page.getByLabel('Name', {exact: true})).toHaveValue('Unsaved Customer intent');
  await page.screenshot({path: '../../.tmp/reference-stale.png', fullPage: true});
  await enter('/settings/profile');
  await page.getByLabel('Display name', {exact: true}).fill('Synthetic Operator');
  await page.getByRole('button', {name: 'Save display name'}).click();
  await expect(page.locator('.shell-session')).toContainText('Synthetic Operator');
  await enter('/settings/preferences');
  await expect(page.getByText('DEFAULT · No persisted override')).toBeVisible();
  await page.getByRole('button', {name: 'Save appearance preference explicitly'}).click();
  await expect(page.getByText('PERSISTED · revision 1')).toBeVisible();
  assert.equal(await page.evaluate(() => document.documentElement.dataset.appearance), 'core-dark');
  const contact = await create('contact', 'Optional Contact');
  await expect(page.getByText('No channels. This Contact remains valid.')).toBeVisible();
  await page.getByLabel('New email').fill('first@example.com');
  await page.getByRole('button', {name: 'Add email channel', exact: true}).click();
  await expect(page.getByText('first@example.com', {exact: true}).first()).toBeVisible();
  await page.getByLabel('New email').fill('second@example.com');
  await page.getByRole('button', {name: 'Add email channel', exact: true}).click();
  await page.getByRole('button', {name: 'Check current channel usability'}).click();
  await expect(page.getByRole('status').filter({hasText: 'MULTIPLE_USABLE · 2 usable channels'})).toBeVisible();
  await page.getByLabel('Current / proposed Customer').selectOption(first);
  await page.getByLabel('Affiliation reason category').fill('operator_link');
  await page.getByRole('button', {name: 'Change affiliation explicitly'}).click();
  await expect(page.getByText('Customer One · current', {exact: true})).toBeVisible();
  await page.getByRole('button', {name: 'Edit channel', exact: true}).first().click();
  await page.getByLabel('Corrected email').fill('corrected@example.com');
  await page.getByRole('button', {name: 'Save channel correction'}).click();
  await expect(page.getByText('corrected@example.com', {exact: true}).first()).toBeVisible();
  const dispatch = await create('dispatch_location', 'Standalone Dispatch', async () => page.getByLabel('Standalone address').fill('Synthetic address\nSecond line'));
  await page.getByLabel('Lifecycle reason category').fill('operator_archive');
  await page.getByRole('button', {name: 'Preview archive dependencies'}).click();
  await expect(page.getByRole('status').filter({hasText: 'Exact blocker count: 0 · Preview eligible'})).toBeVisible();
  await page.getByRole('button', {name: 'Archive reference…'}).click();
  await page.getByRole('dialog').getByRole('button', {name: 'Confirm lifecycle operation'}).click();
  await expect(page.getByLabel('Name', {exact: true})).toBeDisabled();
  await page.getByLabel('Lifecycle reason category').fill('operator_reactivate');
  await page.getByRole('button', {name: 'Reactivate reference…'}).click();
  await page.getByRole('dialog').getByRole('button', {name: 'Confirm lifecycle operation'}).click();
  await expect(page.getByLabel('Name', {exact: true})).toBeEnabled();
  await expect(page.getByRole('region', {name: 'Context and history'})).toContainText('active');
  await page.screenshot({path: '../../.tmp/reference-1440.png', fullPage: true});
  await page.setViewportSize({width: 390, height: 844});
  await page.getByRole('group', {name: 'Reference data pane'}).getByRole('button', {name: 'Reference work', exact: true}).click();
  await expect(page.getByLabel('Name', {exact: true})).toHaveValue('Standalone Dispatch');
  await page.getByRole('group', {name: 'Reference data pane'}).getByRole('button', {name: 'Context and history', exact: true}).click();
  await expect(page.getByRole('heading', {name: 'Address source'})).toBeVisible();
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await page.screenshot({path: '../../.tmp/reference-390.png', fullPage: true});
  await page.getByRole('button', {name: 'Customers', exact: true}).click();
  await expect(page.getByRole('group', {name: 'Reference data pane'}).getByRole('button', {name: 'Customers', exact: true})).toHaveAttribute('aria-pressed', 'true');
  await page.getByRole('button', {name: 'Open Customer One · active · revision 1'}).click();
  await expect(page.getByRole('group', {name: 'Reference data pane'}).getByRole('button', {name: 'Reference work', exact: true})).toHaveAttribute('aria-pressed', 'true');
  await expect(page.getByLabel('Name', {exact: true})).toHaveValue('Customer One');
  await page.setViewportSize({width: 1440, height: 1000});
  for (let i = 0; i < 53; i++) {
    const result = await nativeApi('/reference/customer-organizations', {command_id: crypto.randomUUID(), name: 'Paged Customer'});
    assert.equal(result.status, 200);
  }
  await enter('/settings/reference-data/customer_organization');
  await page.getByLabel('Match name').fill('Paged Customer');
  await page.getByRole('button', {name: 'Find candidates'}).click();
  await expect(page.getByRole('status').filter({hasText: 'AMBIGUOUS · 53 exact candidates'})).toBeVisible();
  const candidatePane = page.getByRole('region', {name: 'Customers', exact: true});
  await candidatePane.getByRole('button', {name: 'Next page', exact: true}).last().click();
  await expect(candidatePane.getByText('3 records in this page · 53 matching records')).toBeVisible();
  await expect(page.getByRole('status').filter({hasText: 'AMBIGUOUS · 53 exact candidates'})).toBeVisible();
  await page.getByRole('button', {name: 'Profile', exact: true}).click();
  await page.goBack();
  await expect(page.getByLabel('Match name')).toHaveValue('Paged Customer');
  await expect(candidatePane.getByText('3 records in this page · 53 matching records')).toBeVisible();
  const current = await nativeApi('/reference/customer-organizations/' + first, undefined, 'GET');
  let revision = current.value.revision;
  for (let i = 0; i < 51; i++) {
    const result = await nativeApi('/reference/customer-organizations/' + first + '/customer-account-code', {command_id: crypto.randomUUID(), base_revision: revision, account_code: 'UI-HISTORY-' + i}, 'PUT');
    assert.equal(result.status, 200); revision = result.value.revision;
  }
  await enter('/settings/reference-data/customer_organization/' + first);
  const history = page.getByRole('region', {name: 'Context and history'});
  await expect(history.getByText('50 records in this page · 52 matching records')).toBeVisible();
  await history.getByRole('button', {name: 'Next page', exact: true}).click();
  await expect(history.getByText('2 records in this page · 52 matching records')).toBeVisible();
  await enter('/settings/reference-data/dispatch_location/' + process.argv[3]);
  await expect(page.getByText('Site-derived address · UNAVAILABLE.', {exact: false})).toBeVisible();
  assert.equal(await page.getByLabel('Standalone address').count(), 0);
  await page.getByLabel('Name', {exact: true}).fill('Site descriptive update');
  await page.getByRole('button', {name: 'Save name', exact: true}).click();
  await expect(page.getByLabel('Name', {exact: true})).toHaveValue('Site descriptive update');
  for (const width of [1040, 1039]) {
    await page.setViewportSize({width, height: 900});
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await page.screenshot({path: '../../.tmp/reference-' + width + '.png', fullPage: true});
  }
  await page.emulateMedia({forcedColors: 'active'});
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await page.screenshot({path: '../../.tmp/reference-forced-colors.png', fullPage: true});
  assert.deepEqual(errors, []);
  console.log(JSON.stringify({first, second, contact, dispatch, checked: 'Reference/Settings live workflows, recovery/stale intent, narrow pane state'}));
} finally {await browser.close();}
