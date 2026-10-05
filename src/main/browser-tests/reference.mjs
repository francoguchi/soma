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
async function showMatching() {
  const disclosure = page.getByText('Find by exact evidence', {exact: true}).filter({visible: true});
  if (!await disclosure.evaluate(node => node.parentElement.open)) await disclosure.click();
}
async function noOverflow() {assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));}
async function settingsGeometry() {
  for (const width of [1440, 1040, 1039, 390]) {
    await page.setViewportSize({width, height: 1000});
    for (const route of ['profile', 'preferences']) {
      await enter('/settings/' + route);
      await expect(page.getByRole(route === 'profile' ? 'textbox' : 'combobox', {name: route === 'profile' ? 'Display name' : 'Appearance preference', exact: true})).toBeVisible();
      const grid = page.locator('.diagnostics-grid');
      assert.equal(await grid.locator(':scope > section').count(), 1, route + ': no unnecessary context panel');
      const geometry = await grid.evaluate(node => {
        const panel = node.firstElementChild, rect = panel.getBoundingClientRect();
        const body = panel.querySelector('.panel-body'), last = body.lastElementChild.getBoundingClientRect();
        return {height: rect.height, width: rect.width, trailing: rect.bottom - last.bottom, columns: getComputedStyle(node).gridTemplateColumns.split(' ').length, border: getComputedStyle(panel).borderRightWidth};
      });
      assert.equal(geometry.columns, 1);
      assert.equal(geometry.border, '0px', route + ': unboxed form');
      assert(geometry.height < 500, route + ': content-sized form');
      assert(geometry.trailing < 65, route + ': no excess space below form');
      assert(geometry.width <= 832, route + ': bounded form width');
      await expect(page.locator('.shell-session')).toContainText('Synthetic Operator');
      await expect(page.getByRole('contentinfo', {name: 'Operator status'})).toContainText('READY');
      await expect(page.getByRole('group', {name: 'Settings pane', exact: true})).toBeHidden();
      if (route === 'preferences') {
        await expect(page.getByRole('combobox', {name: 'Preference', exact: true})).toHaveText('Appearance');
        assert(!/PERSISTED|semantic.owner|persisted override|revision [0-9]/iu.test(await grid.innerText()));
      }
      await noOverflow();
      await page.screenshot({path: '../../.tmp/settings-' + route + '-' + width + '.png', fullPage: true});
    }
  }
  await page.setViewportSize({width: 1440, height: 1000});
}
async function referenceGeometry(identities) {
  for (const width of [1440, 1040, 1039, 390]) {
    await page.setViewportSize({width, height: 1000});
    for (const [kind, id] of Object.entries(identities)) {
      for (const mode of ['browse', 'create', 'open']) {
        await enter('/settings/reference-data/' + kind + (mode === 'browse' ? '' : '/' + (mode === 'create' ? 'new' : id)));
        const surface = page.locator('[data-reference-mode]'), grid = surface.locator('.diagnostics-grid');
        await expect(surface).toHaveAttribute('data-reference-mode', mode);
        await expect(page.getByRole('group', {name: 'Reference data types'})).toBeVisible();
        assert.equal(await page.getByRole('group', {name: 'Reference data types'}).getByRole('button').count(), 3);
        const work = grid.locator(':scope > #console-work'), evidence = grid.locator(':scope > #console-evidence');
        assert.equal(await evidence.count(), mode === 'open' ? 1 : 0, mode + ': evidence requires accepted identity');
        assert.equal(await work.count(), mode === 'browse' ? 0 : 1, mode + ': no empty work pane');
        if (mode === 'browse') {
          await expect(page.getByRole('grid', {name: 'Records'}).first()).toBeVisible();
          await expect(page.getByRole('group', {name: 'Collection actions'})).toBeVisible();
          const sizes = await grid.evaluate(node => ({grid: node.getBoundingClientRect().width, main: node.closest('main').clientWidth, pane: node.firstElementChild.getBoundingClientRect().width}));
          assert(Math.abs(sizes.grid - sizes.pane) < 2, 'Browse occupies full grid width');
          assert(sizes.grid > sizes.main * .9, 'Browse occupies full workspace width');
          if (kind !== 'dispatch_location') assert.equal(await page.getByRole('textbox', {name: 'Match name', exact: true}).count(), 0);
        } else {
          await expect(page.getByLabel('Name', {exact: true})).toBeVisible();
          if (mode === 'create') {
            await expect(page.getByLabel('Name', {exact: true})).toHaveValue('');
            await expect(grid.locator(':scope > #console-records')).toBeHidden();
            await expect(work.getByRole('button', {name: /^Create (Customer|Contact|Dispatch Location)$/u})).toBeVisible();
          } else {
            if (width < 1040) await page.getByRole('group', {name: 'Reference data pane'}).getByRole('button', {name: 'Context and history', exact: true}).click();
            await expect(evidence.getByText('Immutable identity', {exact: true})).toBeVisible();
            if (width < 1040) await page.getByRole('group', {name: 'Reference data pane'}).getByRole('button', {name: 'Reference work', exact: true}).click();
            assert.equal(await grid.locator(':scope > section').count(), 3);
          }
        }
        assert.equal(await grid.locator(':scope > section:visible').count(), mode === 'open' && width >= 1040 ? 3 : 1);
        assert.equal(await grid.evaluate(node => getComputedStyle(node).gridTemplateColumns.split(' ').length), mode === 'open' && width >= 1040 ? 3 : 1);
        await expect(surface.getByRole('status').filter({hasText: /Loading|Refreshing/u})).toHaveCount(0);
        await expect(page.getByRole('contentinfo', {name: 'Operator status'})).toContainText('READY');
        await noOverflow();
        await page.screenshot({path: '../../.tmp/reference-' + kind + '-' + mode + '-' + width + '.png', fullPage: true});
        if (mode === 'open' && width < 1040) {
          for (const pane of [kind === 'customer_organization' ? 'Customers' : kind === 'contact' ? 'Contacts' : 'Dispatch Locations', 'Context and history']) {
            await page.getByRole('group', {name: 'Reference data pane'}).getByRole('button', {name: pane, exact: true}).click();
            await expect(page.getByRole('region', {name: pane, exact: true})).toBeVisible();
            await noOverflow();
            await page.screenshot({path: '../../.tmp/reference-' + kind + '-open-' + width + '-' + (pane === 'Context and history' ? 'evidence' : 'collection') + '.png', fullPage: true});
          }
        }
      }
    }
  }
  await page.setViewportSize({width: 1440, height: 1000});
}
async function collectionReturnState() {
  const pane = page.locator('#console-records'), records = pane.getByRole('grid', {name: 'Records'}).first();
  for (const width of [1440, 390]) {
    await page.setViewportSize({width, height: 1000});
    const row = records.getByRole('row').nth(5);
    await row.click();
    await records.evaluate(node => {node.scrollTop = 120;});
    const before = await records.evaluate(node => ({scroll: node.scrollTop, rows: Array.from(node.children).map(row => row.textContent), selected: node.querySelector('[aria-selected=true]').textContent}));
    assert(before.scroll > 0, 'Return test must exercise real collection scroll');
    await row.press('Enter');
    await expect(page.locator('[data-reference-mode]')).toHaveAttribute('data-reference-mode', 'open');
    await expect(page.getByLabel('Name', {exact: true})).toBeVisible();
    await page.getByRole('button', {name: 'Back to list', exact: true}).click();
    await expect(page.locator('[data-reference-mode]')).toHaveAttribute('data-reference-mode', 'browse');
    assert.equal(await page.locator('#console-work, #console-evidence').count(), 0);
    await expect(page.getByRole('textbox', {name: 'Match name', exact: true})).toHaveValue('Paged Customer');
    await expect(pane.getByText(/3 records in this page.*53 matching records/u)).toBeVisible();
    const after = await records.evaluate(node => ({scroll: node.scrollTop, rows: Array.from(node.children).map(row => row.textContent), selected: node.querySelector('[aria-selected=true]').textContent}));
    assert.deepEqual(after, before, 'Browse/Open/Browse retains collection rows, selection and scroll');
    await page.getByRole('group', {name: 'Collection actions'}).getByRole('button', {name: 'New Customer', exact: true}).click();
    await expect(page.locator('[data-reference-mode]')).toHaveAttribute('data-reference-mode', 'create');
    assert.equal(await page.locator('#console-evidence').count(), 0);
    await page.getByRole('button', {name: 'Back to list', exact: true}).click();
    assert.deepEqual(await records.evaluate(node => ({scroll: node.scrollTop, rows: Array.from(node.children).map(row => row.textContent), selected: node.querySelector('[aria-selected=true]').textContent})), before, 'Create cancel retains collection state');
  }
  await page.setViewportSize({width: 1440, height: 1000});
  await pane.getByRole('button', {name: 'Next page', exact: true}).first().click();
  await expect(records.getByRole('row')).toHaveCount(6);
  const pageRows = await records.innerText();
  await records.getByRole('row').first().dblclick();
  await expect(page.getByLabel('Name', {exact: true})).toBeVisible();
  await page.getByRole('button', {name: 'Back to list', exact: true}).click();
  assert.equal(await records.innerText(), pageRows, 'Collection cursor/page survives open/return');
  await expect(page.getByRole('textbox', {name: 'Match name', exact: true})).toHaveValue('Paged Customer');
}
async function create(kind, name, extra = null) {
  await enter('/settings/reference-data/' + kind + '/new');
  await page.getByLabel('Name', {exact: true}).fill(name);
  if (extra) await extra();
  await page.getByRole('button', {name: 'Create ' + (kind === 'customer_organization' ? 'Customer' : kind === 'contact' ? 'Contact' : 'Dispatch Location'), exact: true}).click();
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
  await showMatching();
  await page.getByRole('textbox', {name: 'Match Account Code', exact: true}).fill('UI-CODE');
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
  await page.getByRole('button', {name: 'Refresh', exact: true}).click();
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
  await expect(page.getByText('Using the default appearance.')).toBeVisible();
  await page.getByRole('button', {name: 'Save appearance preference'}).click();
  await expect(page.getByText('Using your saved appearance preference.')).toBeVisible();
  assert.equal(await page.evaluate(() => document.documentElement.dataset.appearance), 'core-dark');
  await settingsGeometry();
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
  await expect(page.locator('[data-reference-mode]')).toHaveAttribute('data-reference-mode', 'browse');
  assert.equal(await page.locator('#console-work, #console-evidence').count(), 0);
  await page.getByRole('button', {name: 'Open Customer One · active · revision 1'}).click();
  await expect(page.getByRole('group', {name: 'Reference data pane'}).getByRole('button', {name: 'Reference work', exact: true})).toHaveAttribute('aria-pressed', 'true');
  await expect(page.getByLabel('Name', {exact: true})).toHaveValue('Customer One');
  await page.setViewportSize({width: 1440, height: 1000});
  for (let i = 0; i < 53; i++) {
    const result = await nativeApi('/reference/customer-organizations', {command_id: crypto.randomUUID(), name: 'Paged Customer'});
    assert.equal(result.status, 200);
  }
  await enter('/settings/reference-data/customer_organization');
  await showMatching();
  await page.getByRole('textbox', {name: 'Match name', exact: true}).fill('Paged Customer');
  await page.getByRole('button', {name: 'Find candidates'}).click();
  await expect(page.getByRole('status').filter({hasText: 'AMBIGUOUS · 53 exact candidates'})).toBeVisible();
  const candidatePane = page.getByRole('region', {name: 'Customers', exact: true});
  await candidatePane.getByRole('button', {name: 'Next page', exact: true}).last().click();
  await expect(candidatePane.getByText('3 records in this page · 53 matching records')).toBeVisible();
  await expect(page.getByRole('status').filter({hasText: 'AMBIGUOUS · 53 exact candidates'})).toBeVisible();
  await page.getByRole('button', {name: 'Profile', exact: true}).click();
  await page.goBack();
  await expect(page.getByRole('textbox', {name: 'Match name', exact: true})).toHaveValue('Paged Customer');
  await expect(candidatePane.getByText('3 records in this page · 53 matching records')).toBeVisible();
  await collectionReturnState();
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
  await referenceGeometry({customer_organization: first, contact, dispatch_location: dispatch});
  await enter('/settings/reference-data/dispatch_location/' + process.argv[3]);
  await expect(page.getByText('Site-derived address · UNAVAILABLE.', {exact: false})).toBeVisible();
  assert.equal(await page.getByLabel('Standalone address').count(), 0);
  await page.getByLabel('Name', {exact: true}).fill('Site descriptive update');
  await page.getByRole('button', {name: 'Save name', exact: true}).click();
  await expect(page.getByLabel('Name', {exact: true})).toHaveValue('Site descriptive update');
  for (const width of [1040, 1039]) {
    await page.setViewportSize({width, height: 900});
    const grid = page.locator('.diagnostics-grid[data-pane-layout=workbench]');
    assert.equal(await grid.evaluate(node => getComputedStyle(node).gridTemplateColumns.split(' ').length), width >= 1040 ? 3 : 1);
    assert.equal(await grid.locator(':scope > section:visible').count(), width >= 1040 ? 3 : 1);
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await page.screenshot({path: '../../.tmp/reference-' + width + '.png', fullPage: true});
  }
  await page.emulateMedia({forcedColors: 'active'});
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await page.screenshot({path: '../../.tmp/reference-forced-colors.png', fullPage: true});
  assert.deepEqual(errors, []);
  console.log(JSON.stringify({first, second, contact, dispatch, checked: 'Reference/Settings live workflows, recovery/stale intent, narrow pane state'}));
} finally {await browser.close();}
