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
  const button = page.getByRole('button', {name: 'Advanced search', exact: true});
  if (await button.getAttribute('aria-expanded') === 'false') await button.click();
}
async function noOverflow() {assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));}
async function tabsGrammar() {
  const tabs = page.getByRole('navigation', {name: 'Settings sections'});
  await expect(tabs.getByRole('link')).toHaveCount(3);
  const current = tabs.locator('[aria-current=page]');
  await expect(current).toHaveCount(1);
  const style = await current.evaluate(node => ({border: getComputedStyle(node).borderBottomWidth, weight: getComputedStyle(node).fontWeight, box: getComputedStyle(node).borderTopWidth}));
  assert.equal(style.border, '2px'); assert.equal(style.box, '0px'); assert(Number(style.weight) >= 600);
  await current.focus();
  assert.equal(await current.evaluate(node => getComputedStyle(node).outlineStyle), 'solid', 'keyboard focus is distinct from current underline');
  await current.evaluate(node => node.blur());
}
async function unboxedForm(surface, command) {
  assert.equal(await surface.locator('.panel, .diagnostics-grid').count(), 0);
  const geometry = await surface.evaluate(node => ({height: node.getBoundingClientRect().height, width: node.getBoundingClientRect().width, border: getComputedStyle(node).borderLeftWidth}));
  assert.equal(geometry.border, '0px'); assert(geometry.height < 650); assert(geometry.width <= 705);
  const button = await command.boundingBox(), field = await surface.locator('input,select').first().boundingBox();
  assert(button.width < field.width * .8, 'command must remain compact rather than stretch to form width');
  await expect(surface.locator('.section-heading [data-icon]').first()).toBeVisible();
}
async function settingsGeometry() {
  for (const width of [1440, 1040, 1039, 390]) {
    await page.setViewportSize({width, height: 1000});
    for (const route of ['profile', 'preferences']) {
      await enter('/settings/' + route);
      await expect(page.getByRole('heading', {name: 'Settings', exact: true})).toBeVisible();
      await expect(page.getByRole(route === 'profile' ? 'textbox' : 'combobox', {name: route === 'profile' ? 'Display name' : 'Theme', exact: true})).toBeVisible();
      const surface = page.locator('[data-settings-section=' + route + ']');
      assert.equal(await page.locator('.diagnostics-grid, [data-pane-body]').count(), 0);
      await unboxedForm(surface, surface.getByRole('button', {name: route === 'profile' ? 'Save display name' : 'Save appearance', exact: true}));
      await tabsGrammar();
      await expect(page.locator('.shell-session')).toContainText('Synthetic Operator');
      await expect(page.getByRole('contentinfo', {name: 'Operator status'})).toContainText('READY');
      if (route === 'preferences') {
        await expect(page.getByRole('combobox', {name: 'Preference', exact: true})).toHaveCount(0);
        await expect(page.getByRole('heading', {name: 'Appearance', exact: true})).toBeVisible();
        assert(!/PERSISTED|semantic.owner|persisted override|revision [0-9]/iu.test(await surface.innerText()));
      }
      await noOverflow();
      await page.screenshot({path: '../../.tmp/settings-' + route + '-' + width + '.png', fullPage: true});
    }
  }
  await page.setViewportSize({width: 1440, height: 1000});
}
async function browseGrammar(kind, empty = false) {
  assert.equal(await page.locator('.diagnostics-grid, .panel, #console-work, #console-evidence').count(), 0);
  const navigation = page.getByRole('navigation', {name: 'Reference data types'});
  await expect(navigation.getByRole('link')).toHaveCount(3);
  const actions = page.getByRole('group', {name: 'Collection actions'});
  await expect(actions).toBeVisible();
  assert.equal(await navigation.getByRole('button').count(), 0);
  await expect(actions.locator('.action-command')).toHaveCount(1);
  await expect(actions.locator('.action-quiet')).toHaveText('Refresh');
  const collection = page.locator('[data-reference-collection]');
  const search = page.getByRole('search').filter({visible: true});
  await expect(search).toBeVisible();
  const input = search.getByRole('textbox');
  await expect(input).toHaveCount(1);
  if (empty) {await expect(search).toHaveAttribute('data-search-source', 'empty'); await expect(input).toBeDisabled(); await expect(search).toContainText('No active records to search yet.');}
  else if (kind === 'customer_organization') {await expect(search).toHaveAttribute('data-search-source', 'available'); await expect(input).toBeEnabled();}
  else {await expect(search).toHaveAttribute('data-search-source', 'unavailable'); await expect(input).toBeDisabled();}
  await expect(collection.getByRole('button', {name: 'Advanced search', exact: true})).toHaveAttribute('aria-expanded','false');
  await expect(collection.getByRole('textbox', {name:'Match name',exact:true})).toHaveCount(0);
  if (!empty) {await expect(collection.getByRole('grid',{name:'Records'})).toHaveCount(1); assert((await search.boundingBox()).y < (await collection.getByRole('grid', {name: 'Records'}).boundingBox()).y);}
  if (empty) {
    const label = kind === 'customer_organization' ? 'Customers' : 'Contacts';
    await expect(collection.getByText('No ' + label + ' yet.', {exact: true})).toBeVisible();
    assert(!/0 records|0 matching records|No records in this page/u.test(await collection.innerText()));
    assert((await collection.boundingBox()).height < 650, 'empty browse ends with its information');
  } else {
    await expect(collection.getByRole('columnheader', {name: 'Name', exact: true})).toBeVisible();
    await expect(collection.getByRole('columnheader', {name: 'Revision', exact: true})).toBeVisible();
  }
}
async function referenceGeometry(identities) {
  for (const width of [1440, 1040, 1039, 390]) {
    await page.setViewportSize({width, height: 1000});
    for (const [kind, id] of Object.entries(identities)) {
      for (const mode of ['browse', 'create', 'open']) {
        await enter('/settings/reference-data/' + kind + (mode === 'browse' ? '' : '/' + (mode === 'create' ? 'new' : id)));
        const surface = page.locator('[data-reference-mode]'), grid = surface.locator('.diagnostics-grid');
        await expect(surface).toHaveAttribute('data-reference-mode', mode);
        await expect(page.getByRole('navigation', {name: 'Reference data types'})).toBeVisible();
        assert.equal(await page.locator('#console-work, #console-evidence').count(), mode === 'open' ? 2 : 0);
        if (mode === 'browse') {
          await expect(page.getByRole('grid', {name: 'Records'}).first()).toBeVisible();
          await browseGrammar(kind);
        } else if (mode === 'create') {
          await expect(page.getByLabel('Name', {exact: true})).toHaveValue('');
          assert.equal(await page.locator('.panel, .diagnostics-grid, [data-reference-collection]').count(), 0);
          const form = page.locator('[data-create-surface]');
          await expect(form.getByRole('button', {name: 'Back to list', exact: true})).toHaveCount(0);
          await expect(form.getByRole('button', {name: 'Cancel', exact: true})).toBeVisible();
          await unboxedForm(form, form.getByRole('button', {name: /^Create (Customer|Contact|Dispatch Location)$/u}));
        } else {
          await expect(page.getByLabel('Name', {exact: true})).toBeVisible();
          await expect(surface.locator('[data-reference-navigation]').getByRole('button', {name: 'Back to list'})).toBeVisible();
          await expect(grid.getByRole('button', {name: 'Back to list'})).toHaveCount(0);
          // Opened identity is a separate marker from explicit selection.
          await expect(page.locator('[data-reference-collection] > div:not([hidden]) [role=grid]')).toHaveCount(1);
          await expect(page.locator('[data-reference-collection] [role=row][aria-current=true]')).toHaveCount(1);
          await expect(page.locator('[data-reference-collection] > div:not([hidden])').getByRole('button',{name:'Advanced search',exact:true,includeHidden:true})).toHaveAttribute('aria-expanded','false');
          assert.equal(await grid.locator(':scope > section').count(), 3);
          assert.equal(await grid.locator(':scope > section:visible').count(), width >= 1040 ? 3 : 1);
          assert.equal(await grid.evaluate(node => getComputedStyle(node).gridTemplateColumns.split(' ').length), width >= 1040 ? 3 : 1);
          const geometry = await grid.evaluate(node => ({bottom: node.getBoundingClientRect().bottom, mainBottom: node.closest('main').getBoundingClientRect().bottom, height: node.getBoundingClientRect().height}));
          assert(geometry.height > 550); assert(Math.abs(geometry.bottom - geometry.mainBottom) < 30, 'Open owns remaining usable height');
          if (width >= 1040) {
            for (const panel of await grid.locator(':scope > section').all()) {
              const body = panel.locator('[data-pane-body]'), header = panel.locator(':scope > h2');
              const before = await header.boundingBox();
              await body.evaluate(node => {node.scrollTop = 150;});
              assert.deepEqual(await header.boundingBox(), before, 'pane headers stay fixed while bodies scroll');
              await body.evaluate(node => {node.scrollTop = 0;});
            }
          }
          await expect(grid.locator('#console-work .section-heading [data-icon]').first()).toBeVisible();
          assert.equal(await grid.locator('.panel .panel').count(), 0, 'no nested panel cards');
          if (width >= 1040) {
            const currentRow = page.locator('[data-reference-collection] [role=row][aria-current=true]');
            assert((await currentRow.locator('[role=gridcell]').first().boundingBox()).width >= 72, 'opened marker must not squeeze collection names into vertical letters');
            assert((await currentRow.boundingBox()).height < 100, 'simple opened row remains dense at split boundary');
            assert((await page.locator('#console-evidence .compact-evidence dd').first().boundingBox()).width >= 100, 'evidence labels leave readable value width at split boundary');
          }
        }
        await expect(surface.getByRole('status').filter({hasText: /Loading|Refreshing/u})).toHaveCount(0);
        await expect(page.getByRole('contentinfo', {name: 'Operator status'})).toContainText('READY');
        await tabsGrammar(); await noOverflow();
        await page.screenshot({path: '../../.tmp/reference-' + kind + '-' + mode + '-' + width + '.png', fullPage: true});
        if (mode === 'open' && width < 1040) {
          for (const pane of [kind === 'customer_organization' ? 'Customers' : kind === 'contact' ? 'Contacts' : 'Dispatch Locations', 'Evidence & history']) {
            await page.getByRole('group', {name: 'Reference data pane'}).getByRole('button', {name: pane, exact: true}).click();
            await expect(page.getByRole('region', {name: pane, exact: true})).toBeVisible();
            await noOverflow();
            await page.screenshot({path: '../../.tmp/reference-' + kind + '-open-' + width + '-' + (pane === 'Evidence & history' ? 'evidence' : 'collection') + '.png', fullPage: true});
          }
        }
      }
    }
  }
  await page.setViewportSize({width: 1440, height: 1000});
}
async function collectionReturnState() {
  const pane = page.locator('[data-reference-collection]'), records = pane.locator('[data-reference-records]').getByRole('grid', {name: 'Records'});
  for (const width of [1440, 390]) {
    await page.setViewportSize({width, height: 1000});
    const row = records.locator('[role=row]:not([data-collection-header])').nth(5);
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
    await expect(page.getByRole('textbox', {name: 'Search Customers', exact: true})).toHaveValue('');
    await expect(pane.getByRole('grid',{name:'Records'})).toHaveCount(1);
    const after = await records.evaluate(node => ({scroll: node.scrollTop, rows: Array.from(node.children).map(row => row.textContent), selected: node.querySelector('[aria-selected=true]').textContent}));
    assert.deepEqual(after, before, 'Browse/Open/Browse retains collection rows, selection and scroll');
    await expect(row).toBeFocused();
    await page.getByRole('group', {name: 'Collection actions'}).getByRole('button', {name: 'New Customer', exact: true}).click();
    await expect(page.locator('[data-reference-mode]')).toHaveAttribute('data-reference-mode', 'create');
    assert.equal(await page.locator('#console-evidence').count(), 0);
    await page.getByRole('button', {name: 'Cancel', exact: true}).click();
    await expect(page.getByRole('group', {name: 'Collection actions'}).getByRole('button', {name: 'New Customer', exact: true})).toBeFocused();
    assert.deepEqual(await records.evaluate(node => ({scroll: node.scrollTop, rows: Array.from(node.children).map(row => row.textContent), selected: node.querySelector('[aria-selected=true]').textContent})), before, 'Create cancel retains collection state');
  }
  await page.setViewportSize({width: 1440, height: 1000});
  await pane.locator('[data-reference-records]').getByRole('button', {name: 'Next page', exact: true}).click();
  await expect(records.locator('[role=row]:not([data-collection-header])')).toHaveCount(6);
  const pageRows = await records.locator('[data-record-name]').allTextContents();
  await records.locator('[role=row]:not([data-collection-header])').first().dblclick();
  await expect(page.getByLabel('Name', {exact: true})).toBeVisible();
  await page.getByRole('button', {name: 'Back to list', exact: true}).click();
  assert.deepEqual(await records.locator('[data-record-name]').allTextContents(), pageRows, 'Collection cursor/page survives open/return');
  await expect(page.getByRole('textbox', {name: 'Search Customers', exact: true})).toHaveValue('');
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
  await expect(page.getByRole('heading', {name: 'Settings'})).toBeVisible();
  assert.equal(await page.getByRole('group', {name: 'Workspaces', exact: true}).getByRole('button').count(), 6);
  await expect(page.getByRole('group', {name: 'Workspaces', exact: true}).getByRole('button', {name: 'Settings', exact: true})).toBeEnabled();
  assert.equal(await page.getByRole('group', {name: 'Workspaces', exact: true}).getByRole('button', {name: 'Customers', exact: true}).count(), 0);
  for (const kind of ['customer_organization', 'contact']) {
    for (const width of [1440, 390]) {
      await page.setViewportSize({width, height: 1000});
      await enter('/settings/reference-data/' + kind);
      await browseGrammar(kind, true); await tabsGrammar(); await noOverflow();
      await expect(page.locator('[data-reference-collection]').getByRole('status').filter({hasText: /Loading|Refreshing/u})).toHaveCount(0);
      await page.screenshot({path: '../../.tmp/reference-' + kind + '-empty-' + width + '.png', fullPage: true});
    }
  }
  await page.setViewportSize({width: 1440, height: 1000});
  const first = await create('customer_organization', 'Customer One', async () => page.getByLabel('Initial Account Code (optional)').fill('UI-CODE'));
  const second = await create('customer_organization', 'Customer Two');
  await page.getByLabel('Account Code', {exact: true}).fill('UI-CODE');
  await page.getByRole('button', {name: 'Set Account Code', exact: true}).click();
  await expect(page.getByRole('alert').filter({hasText: 'ACCOUNT_CODE_CONFLICT_REVIEW'}).first()).toBeVisible();
  await expect(page.getByLabel('Account Code', {exact: true})).toHaveValue('UI-CODE');
  await page.getByLabel('Account Code reason category').fill('operator_review');
  await page.getByRole('button', {name: 'Load Account Code review'}).click();
  await expect(page.getByText('Exact claimant count: 1')).toBeVisible();
  await page.getByRole('button',{name:'Show claimants in collection',exact:true}).click();
  await expect(page.getByRole('status').filter({hasText:'Unique candidate · 1 exact candidate'})).toBeVisible();
  await expect(page.locator('[data-reference-collection]').getByRole('grid',{name:'Records'})).toHaveCount(1);
  await expect(page.locator('#console-work').getByRole('grid')).toHaveCount(0);
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
  await expect(page.getByRole('status').filter({hasText: 'Ambiguous · 2 exact candidates'})).toBeVisible();
  await expect(page.locator('[data-reference-collection]').getByRole('grid',{name:'Records'})).toHaveCount(1);
  await expect(page.getByRole('button',{name:'Advanced search',exact:true})).toHaveAttribute('aria-expanded','false');
  for (const width of [1440,390]) {
    await page.setViewportSize({width,height:1000}); await noOverflow();
    await page.screenshot({path:'../../.tmp/ux-advanced-ambiguous-'+width+'.png',fullPage:true});
  }
  await page.setViewportSize({width:1440,height:1000});
  await page.getByLabel('Name', {exact: true}).fill('Unsaved Customer intent');
  await page.getByRole('link', {name: 'Profile', exact: true}).click();
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
  await page.getByRole('button', {name: 'Save appearance'}).click();
  await expect(page.getByText('Using your saved appearance preference.')).toBeVisible();
  assert.equal(await page.evaluate(() => document.documentElement.dataset.appearance), 'core-dark');
  await settingsGeometry();
  const contact = await create('contact', 'Optional Contact');
  await expect(page.getByText('No channels yet.')).toBeVisible();
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
  await showMatching();
  await page.getByRole('textbox',{name:'Match email',exact:true}).fill('corrected@example.com');
  await page.getByRole('combobox',{name:'Matching affiliation scope',exact:true}).selectOption(first);
  await page.getByRole('button',{name:'Find candidates',exact:true}).click();
  await expect(page.locator('[data-reference-collection]').getByRole('status').filter({hasText:'Unique candidate · 1 exact candidate'})).toBeVisible();
  await expect(page.locator('[data-reference-collection]').getByRole('grid',{name:'Records'})).toHaveCount(1);
  await page.locator('[data-reference-collection]').getByRole('button',{name:'Clear search',exact:true}).click();
  const anotherContact = await nativeApi('/reference/contacts', {command_id:crypto.randomUUID(), name:'Second Contact',initial_email:null,initial_customer_org_id:null});
  assert.equal(anotherContact.status,200);
  await page.getByRole('button',{name:'Refresh',exact:true}).click();
  const contactList=page.locator('[data-reference-records]').getByRole('grid',{name:'Records'});
  await expect(contactList).toHaveCount(1);
  const secondRow=contactList.getByRole('button',{name:'Open Second Contact',exact:true}).locator('..').locator('..');
  await secondRow.click();
  await expect(page.getByLabel('Name',{exact:true})).toHaveValue('Optional Contact');
  await secondRow.press('Enter');
  await expect(page.getByLabel('Name',{exact:true})).toHaveValue('Second Contact');
  await expect(page.locator('#console-evidence code').first()).toHaveText(anotherContact.value.target_id);
  await expect(contactList).toHaveCount(1);
  await page.getByLabel('Name',{exact:true}).fill('Unsaved Second Contact');
  await contactList.getByRole('button',{name:'Open Optional Contact',exact:true}).click();
  await expect(page.getByRole('dialog',{name:'Leave unsaved changes?'})).toBeVisible();
  await page.getByRole('dialog').getByRole('button',{name:'Cancel',exact:true}).click();
  await expect(page.getByLabel('Name',{exact:true})).toHaveValue('Unsaved Second Contact');
  await page.getByRole('button',{name:'Discard metadata intent',exact:true}).click();
  await contactList.getByRole('button',{name:'Open Optional Contact',exact:true}).click();
  await expect(page.getByLabel('Name',{exact:true})).toHaveValue('Optional Contact');
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
  await expect(page.getByRole('region', {name: 'Evidence & history'})).toContainText('active');
  await page.screenshot({path: '../../.tmp/reference-1440.png', fullPage: true});
  await page.setViewportSize({width: 390, height: 844});
  await page.getByRole('group', {name: 'Reference data pane'}).getByRole('button', {name: 'Details', exact: true}).click();
  await expect(page.getByLabel('Name', {exact: true})).toHaveValue('Standalone Dispatch');
  await page.getByRole('group', {name: 'Reference data pane'}).getByRole('button', {name: 'Evidence & history', exact: true}).click();
  await expect(page.getByRole('heading', {name: 'Address source'})).toBeVisible();
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await page.screenshot({path: '../../.tmp/reference-390.png', fullPage: true});
  await page.getByRole('navigation', {name: 'Reference data types'}).getByRole('link', {name: 'Customers', exact: true}).click();
  await expect(page.locator('[data-reference-mode]')).toHaveAttribute('data-reference-mode', 'browse');
  assert.equal(await page.locator('#console-work, #console-evidence').count(), 0);
  await page.getByRole('button', {name: 'Open Customer One', exact: true}).click();
  await expect(page.getByRole('group', {name: 'Reference data pane'}).getByRole('button', {name: 'Details', exact: true})).toHaveAttribute('aria-pressed', 'true');
  await expect(page.getByLabel('Name', {exact: true})).toHaveValue('Customer One');
  await page.setViewportSize({width: 1440, height: 1000});
  for (let i = 0; i < 53; i++) {
    const result = await nativeApi('/reference/customer-organizations', {command_id: crypto.randomUUID(), name: 'Paged Customer'});
    assert.equal(result.status, 200);
  }
  await enter('/settings/reference-data/customer_organization');
  await page.getByRole('textbox',{name:'Search Customers',exact:true}).fill('No matching UI fixture');
  await page.getByRole('button',{name:'Search',exact:true}).click();
  await expect(page.locator('[data-reference-collection]').getByText('No exact candidates',{exact:true})).toBeVisible();
  await expect(page.getByRole('textbox',{name:'Search Customers',exact:true})).toBeEnabled();
  assert(!/0 records|0 matching|0 exact/u.test(await page.locator('[data-reference-collection]').innerText()));
  for (const width of [1440,390]) {
    await page.setViewportSize({width,height:1000}); await noOverflow();
    await page.screenshot({path:'../../.tmp/ux-no-results-'+width+'.png',fullPage:true});
  }
  await page.setViewportSize({width:1440,height:1000});
  await page.getByRole('textbox', {name: 'Search Customers', exact: true}).fill('Paged Customer');
  await page.getByRole('button', {name: 'Search', exact: true}).click();
  await expect(page.getByRole('status').filter({hasText: 'Ambiguous · 53 exact candidates'})).toBeVisible();
  const candidatePane = page.locator('[data-reference-collection]');
  await candidatePane.getByRole('button', {name: 'Next page', exact: true}).click();
  await expect(candidatePane.getByRole('status').filter({hasText:'53 exact candidates · 3 on this page'})).toBeVisible();
  await expect(page.getByRole('status').filter({hasText: 'Ambiguous · 53 exact candidates'})).toBeVisible();
  await page.getByRole('link', {name: 'Profile', exact: true}).click();
  await page.goBack();
  await expect(page.getByRole('textbox', {name: 'Search Customers', exact: true})).toHaveValue('Paged Customer');
  await expect(candidatePane.getByRole('status').filter({hasText:'53 exact candidates · 3 on this page'})).toBeVisible();
  await expect(candidatePane.getByRole('grid', {name:'Records'})).toHaveCount(1);
  assert(!/matching records|53 records/u.test(await candidatePane.innerText()));
  const searchedRows = await candidatePane.locator('[data-record-name]').allTextContents();
  await candidatePane.getByRole('button', {name:'Open Paged Customer', exact:true}).first().click();
  await expect(page.getByLabel('Name',{exact:true})).toHaveValue('Paged Customer');
  await page.getByRole('button',{name:'Back to list',exact:true}).click();
  assert.deepEqual(await candidatePane.locator('[data-record-name]').allTextContents(), searchedRows);
  await expect(page.getByRole('textbox', {name:'Search Customers',exact:true})).toHaveValue('Paged Customer');
  for (const width of [1440,1040,1039,390]) {
    await page.setViewportSize({width,height:1000}); await noOverflow();
    await page.screenshot({path:'../../.tmp/ux-customer-searched-'+width+'.png',fullPage:true});
  }
  await candidatePane.getByRole('button',{name:'Clear search',exact:true}).click();
  await expect(candidatePane.locator('[data-collection-mode]:visible')).toHaveAttribute('data-collection-mode','browse');
  await expect(candidatePane.getByRole('grid',{name:'Records'})).toHaveCount(1);
  await expect(candidatePane.getByRole('status').filter({hasText:/Loading|Refreshing/u})).toHaveCount(0);
  await collectionReturnState();
  // Archive only the disposable final-page fixtures, leaving broader active records.
  const lastIds=await candidatePane.locator('[data-reference-records]:visible [role=row][data-focus-token]').evaluateAll(rows=>rows.map(row=>row.dataset.focusToken.slice('record:'.length)));
  assert.equal(lastIds.length,6);
  for (const target of lastIds) {
    const outcome=await nativeApi('/reference/customer_organization/'+target+'/archive',{command_id:crypto.randomUUID(),base_revision:1,reason_category:'test_empty_page'});
    assert.equal(outcome.status,200);
  }
  await candidatePane.getByRole('button',{name:'Refresh',exact:true}).click();
  await expect(candidatePane.getByText('No active records on this page. Refresh to reload the list.',{exact:true})).toBeVisible();
  await expect(page.getByRole('textbox',{name:'Search Customers',exact:true})).toBeEnabled();
  await page.screenshot({path:'../../.tmp/ux-empty-page-valid-search.png',fullPage:true});
  const current = await nativeApi('/reference/customer-organizations/' + first, undefined, 'GET');
  let revision = current.value.revision;
  for (let i = 0; i < 51; i++) {
    const result = await nativeApi('/reference/customer-organizations/' + first + '/customer-account-code', {command_id: crypto.randomUUID(), base_revision: revision, account_code: 'UI-HISTORY-' + i}, 'PUT');
    assert.equal(result.status, 200); revision = result.value.revision;
  }
  await enter('/settings/reference-data/customer_organization/' + first);
  const history = page.getByRole('region', {name: 'Evidence & history'});
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
  await expect(page.locator('#console-work').getByRole('heading',{name:'Site descriptive update',exact:true})).toBeVisible();
  await expect(page.locator('[data-reference-mode]').getByRole('status').filter({hasText:/Loading|Refreshing/u})).toHaveCount(0);
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
  for (const route of ['profile', 'preferences', 'reference-data/customer_organization', 'reference-data/contact/new']) {
    await enter('/settings/' + route);
    if (route === 'profile') await expect(page.getByLabel('Display name', {exact: true})).toBeVisible();
    else if (route === 'preferences') await expect(page.getByRole('combobox', {name: 'Theme', exact: true})).toBeVisible();
    else if (route.endsWith('/new')) await expect(page.getByLabel('Name', {exact: true})).toBeVisible();
    else await expect(page.getByRole('grid', {name: 'Records'}).first()).toBeVisible();
    await expect(page.getByRole('status').filter({hasText: /Loading|Refreshing/u})).toHaveCount(0);
    await expect(page.getByRole('contentinfo', {name: 'Operator status'})).toContainText('READY');
    await tabsGrammar(); await noOverflow();
    await page.screenshot({path: '../../.tmp/settings-forced-colors-' + route.replaceAll('/', '-') + '.png', fullPage: true});
  }
  await page.getByRole('navigation', {name: 'Settings sections'}).getByRole('link', {name: 'Preferences', exact: true}).focus();
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(new RegExp('/settings/preferences$'));
  await expect(page.getByRole('heading', {name: 'Appearance', exact: true})).toBeVisible();
  assert.deepEqual(errors, []);
  console.log(JSON.stringify({first, second, contact, dispatch, checked: 'Reference/Settings live workflows, recovery/stale intent, narrow pane state'}));
} finally {await browser.close();}
