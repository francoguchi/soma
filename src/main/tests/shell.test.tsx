import {expect, test} from 'vitest';
import {ApiClient, QueryController} from '../shared/api/client';
import {assertContract} from '../shared/api/validate';
import {displayTime} from '../shared/time';
import {applyAppearance} from '../shared/appearance';
import {Navigation, resolveRoute, type ReturnState} from '../app/router';
import {workspaces, systemDestinations, workspaceState} from '../app/workspaces/registry';
import {hasTextCorruption} from '../shared/text/integrity';
import shellSource from '../app/entry.tsx?raw';
import diagnosticsSource from '../features/system/Diagnostics.tsx?raw';
import workbenchSource from '../shared/components/Workbench.tsx?raw';

test('shared formatter preserves the same UTC fact across timezones', () => {
  const instant = 1704067200;
  expect(displayTime(instant, {timeZone: 'UTC', locale: 'en-US'})).toContain('Jan 1, 2024');
  expect(displayTime(instant, {timeZone: 'America/Guayaquil', locale: 'en-US'})).toContain('Dec 31, 2023');
  expect(displayTime(null)).toBe('Unknown');
  expect(displayTime(NaN)).toBe('Time unavailable');
});
test('unknown appearance falls back deterministically to Core Dark', () => {
  expect(applyAppearance('invalid')).toBe('core-dark');
  expect(document.documentElement.dataset['appearance']).toBe('core-dark');
});
test('closed runtime contract rejects extras, wrong units and malformed identity', () => {
  expect(assertContract('empty-request', {})).toEqual({});
  expect(() => assertContract('empty-request', {extra: true})).toThrow();
  expect(() => assertContract('auth-login-request', {run_id: 'not-a-uuid', password: 'Foundation password 42'})).toThrow();
});
test('superseded query cannot publish even if transport ignores cancellation', async () => {
  const controller = new QueryController<string>();
  const seen: string[] = [];
  let release!: (value: string) => void;
  const older = controller.query(() => new Promise(resolve => {release = resolve;}), value => seen.push(value), () => {});
  await controller.query(async () => 'new', value => seen.push(value), () => {});
  release('old'); await older;
  expect(seen).toEqual(['new']);
});
test('stale tab refuses a new run before any command is submitted', () => {
  const client = new ApiClient(); client.runId = 'old';
  expect(() => client.acceptBootstrap({run_id: 'new'} as never)).toThrow('restarted');
});
test('closed history routes retain owner navigation context without dispatch', () => {
  history.replaceState(null, '', '/system/diagnostics');
  const context: ReturnState = {filters: {query: 'abc'}, activeId: 'a', selectedIds: ['a'], pane: 'evidence', tab: 'history', scrollTop: 80, focusToken: 'record-a'};
  const navigation = new Navigation(() => context);
  expect(resolveRoute('/inventory')?.capability).toBe('inventory');
  navigation.open('/inventory');
  expect(location.pathname).toBe('/inventory');
  expect(() => navigation.open('/unknown/executable')).toThrow();
  history.replaceState(null, '', '/');
});

test('only accepted workspaces define navigation, independent from arbitrary capabilities', () => {
  expect(workspaces.map(item => item.title)).toEqual(['Overview', 'Tickets', 'Objectives', 'Inventory', 'Infrastructure', 'Settings']);
  expect(systemDestinations.map(item => item.title)).toEqual(['Diagnostics']);
  const capabilities = [{id: 'finance', state: 'available', reason: null}, {id: 'tickets', state: 'development', reason: null}] as const;
  expect(workspaceState('tickets', [...capabilities])).toBe('development');
  expect(workspaceState('inventory', [...capabilities])).toBe('unavailable');
  expect(resolveRoute('/finance')).toBeNull();
  expect(resolveRoute('/customers')).toBeNull();
});

test('governed source text is UTF-8 and representative symbols detect wrong-code-page decoding', () => {
  expect(hasTextCorruption('SOMA · Ready — local')).toBe(false);
  expect(hasTextCorruption('SOMA \u00c2\u00b7 Ready')).toBe(true);
  expect(hasTextCorruption('\ufffd')).toBe(true);
  for (const source of [shellSource, diagnosticsSource, workbenchSource]) {
    expect(hasTextCorruption(source)).toBe(false);
  }
});
