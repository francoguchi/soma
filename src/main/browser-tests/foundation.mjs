// Real encrypted Foundation host: no Vite server, API mocks, or donor runtime.
import assert from 'node:assert/strict';
import {chromium, expect} from '@playwright/test';
const origin = process.argv[2];
assert.match(origin, /^http:\/\/127\.0\.0\.1:[1-9][0-9]*$/u);
const browser = await chromium.launch({headless: true, channel: 'chrome'});
const password = 'Synthetic Foundation browser password 42';
try {
  const context = await browser.newContext({viewport: {width: 1366, height: 900}});
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => {assert.equal(new URL(request.url()).origin, origin);});
  await page.goto(origin + '/system/diagnostics');
  await expect(page.getByRole('heading', {name: 'Set up Local Administrator'})).toBeVisible();
  await expect(page.getByLabel('Password', {exact: true})).toBeFocused();
  await page.screenshot({path: '../../.tmp/foundation-setup.png', fullPage: true});
  await page.getByLabel('Password', {exact: true}).fill(password);
  await page.getByLabel('Confirm password').fill(password);
  await page.getByRole('button', {name: 'Create password and sign in'}).click();
  await expect(page.getByRole('heading', {name: 'Diagnostics', exact: true})).toBeVisible();
  await expect(page.getByText('Sanitized logging active')).toBeVisible();
  await expect(page.getByText('Uptime', {exact: true})).toBeVisible();
  assert.equal(await page.locator('.capability-list li').count(), 5);
  await expect(page.getByText('No warnings or errors.', {exact: true})).toBeVisible();
  await expect(page.getByRole('list', {name: 'Runtime chronology'})).toContainText('RUNTIME_READY');
  await expect(page.locator('.status-secondary').getByText('schema M00.005', {exact: true})).toBeVisible();
  await expect(page.getByRole('button', {name: 'Inventory - Not available in this build'})).toBeDisabled();
  assert.equal(await page.evaluate(() => document.documentElement.dataset.appearance), 'core-dark');
  const cookies = await context.cookies();
  assert(cookies.some(cookie => cookie.name === 'soma_session' && cookie.httpOnly && cookie.sameSite === 'Strict' && !cookie.secure));
  await page.screenshot({path: '../../.tmp/foundation-shell.png', fullPage: true});
  await page.goto(origin + '/inventory');
  await expect(page.getByRole('heading', {name: 'Inventory', exact: true})).toBeVisible();
  await expect(page.getByText('Not available in this build.', {exact: true})).toBeVisible();
  await page.getByRole('button', {name: 'Go to Diagnostics'}).click();
  await expect(page.getByRole('heading', {name: 'Diagnostics', exact: true})).toBeVisible();
  await page.goBack();
  await expect(page.getByRole('heading', {name: 'Inventory', exact: true})).toBeVisible();
  await page.goForward();
  await expect(page.getByRole('heading', {name: 'Diagnostics', exact: true})).toBeVisible();
  const navigation = page.getByRole('group', {name: 'Workspaces', exact: true});
  assert.deepEqual(await navigation.getByRole('button').evaluateAll(items => items.map(item => item.querySelector('span').textContent)), ['Overview', 'Tickets', 'Objectives', 'Inventory', 'Infrastructure', 'Settings']);
  assert.equal(await page.getByRole('button', {name: /Finance|Products|Service levels|Workflows|Customers/u}).count(), 0);
  for (const width of [1440, 1040, 1039, 390]) {
    await page.setViewportSize({width, height: 900});
    const wide = width >= 1040;
    await expect(page.locator('.operational-console')).toHaveAttribute('data-layout', wide ? 'split' : 'switcher');
    assert.equal(await page.locator('[data-console-pane]:visible').count(), wide ? 4 : 1);
    assert.equal(await page.locator('[data-pane-active=true]:visible').count(), 1);
    const gridBounds = await page.locator('.diagnostics-grid').boundingBox();
    const stripBounds = await page.getByRole('contentinfo', {name: 'Operator status'}).boundingBox();
    assert(Math.abs(gridBounds.y + gridBounds.height - stripBounds.y) <= 16);
    assert(stripBounds.height <= 32);
    await expect(page.locator('.status-primary')).toContainText('READY');
    if (!wide) {
      await page.getByLabel('Operator status details').click();
      await expect(page.getByLabel('Secondary operator status')).toContainText('schema M00.005');
      await page.getByLabel('Operator status details').click();
    }
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    assert(await page.locator('.main-scroll').evaluate(node => node.getBoundingClientRect().right <= innerWidth));
    assert(await page.getByRole('button', {name: 'Sign out'}).evaluate(node => node.getBoundingClientRect().right <= innerWidth));
    assert(await page.locator('[data-console-pane]:visible').evaluateAll(nodes => nodes.every(node => node.scrollWidth <= node.clientWidth)));

    assert.equal(await page.evaluate(() => /\uFFFD|\u00C2[\u00A0-\u00BF]|\u00C3[\u0080-\u00BF]|\u00E2[\u0080-\u00BF\u20AC\u2122]/u.test(document.body.innerText)), false);
    await page.screenshot({path: `../../.tmp/refinement-${width}.png`, fullPage: true});
    if (!wide) {
      for (const title of ['Runtime activity', 'Capabilities', 'Operator logs', 'Current run']) {
        await page.getByRole('button', {name: title, exact: true}).click();
        await expect(page.getByRole('heading', {name: title, exact: true})).toBeVisible();
      }
    }
  }
  await page.getByRole('button', {name: 'Operator logs', exact: true}).click();
  await expect(page.getByText('Sanitized logging active')).toBeVisible();
  await page.setViewportSize({width: 1040, height: 900});
  await expect(page.locator('[data-console-pane="logs"]')).toBeFocused();
  await page.setViewportSize({width: 1039, height: 900});
  await expect(page.getByRole('button', {name: 'Operator logs', exact: true})).toHaveAttribute('aria-pressed', 'true');
  await expect(page.locator('[data-console-pane="logs"]')).toBeFocused();
  await page.setViewportSize({width: 390, height: 844});
  await page.emulateMedia({forcedColors: 'active', reducedMotion: 'reduce'});
  await expect(page.getByRole('button', {name: 'Open current log'})).toBeVisible();
  await page.screenshot({path: '../../.tmp/refinement-forced-colors.png', fullPage: true});
  await page.emulateMedia({forcedColors: 'none', reducedMotion: 'no-preference'});
  await page.evaluate(() => {const sheet = document.styleSheets[0]; const sizes = Array.from(document.querySelectorAll('body,h1,h2,h3,p,li,dt,dd,code,span,small,time,button,summary,input,label'), node => [node, parseFloat(getComputedStyle(node).fontSize)]); sizes.forEach(([node,size],i) => {node.setAttribute('data-text-zoom',String(i)); sheet.insertRule(`[data-text-zoom=\"${i}\"]{font-size:${size*2}px!important}`,sheet.cssRules.length);});});
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  assert(await page.getByRole('button', {name:'Refresh',exact:true}).evaluate(node => node.getBoundingClientRect().right <= innerWidth));
  await page.screenshot({path: '../../.tmp/refinement-text-200.png', fullPage: true});
  await page.getByRole('button', {name: 'Sign out'}).click();
  await expect(page.getByRole('heading', {name: 'Sign in to SOMA'})).toBeVisible();
  await page.getByLabel('Password', {exact: true}).fill('not the correct password');
  await page.getByRole('button', {name: 'Sign in', exact: true}).click();
  await expect(page.getByRole('alert')).toContainText('password could not be verified');
  await page.getByLabel('Password', {exact: true}).fill(password);
  await page.getByRole('button', {name: 'Sign in', exact: true}).click();
  await expect(page.getByRole('heading', {name: 'Diagnostics', exact: true})).toBeVisible();
  assert.deepEqual(errors, []);
  assert.equal(await page.evaluate(() => localStorage.length + sessionStorage.length), 0);
  console.log('Real Foundation browser setup/login/logout, diagnostics, unavailable routes/history, Core Dark, local resources and mobile reflow passed.');
} finally {await browser.close();}
