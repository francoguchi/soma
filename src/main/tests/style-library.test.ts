import {expect, test} from 'vitest';
import entry from '../styles/soma.css?raw';
import paneStyles from '../styles/primitives/panes.css?raw';
import collectionStyles from '../styles/primitives/collections.css?raw';
import scrollbarStyles from '../styles/primitives/scrollbars.css?raw';
import tokenStyles from '../styles/tokens.css?raw';
import accessibilityStyles from '../styles/components.css?raw';

test('stable stylesheet entry declares ordered Foundation layers and imports shared primitives', () => {
  expect(entry).toContain('@layer reset, tokens, base, primitives, components, utilities, features;');
  for (const primitive of ['actions', 'panes', 'collections', 'forms', 'feedback', 'scrollbars', 'status']) {
    expect(entry).toContain(`./primitives/${primitive}.css`);
  }
});

test('pane focus stays local and current-pane state has no visible ACTIVE badge', () => {
  expect(paneStyles).toContain('outline:none;box-shadow:inset 3px 0 var(--focus)');
  expect(paneStyles).not.toContain('.active-pane-label');
  expect(paneStyles).not.toContain('[data-pane-id]:focus-visible{outline:');
  expect(accessibilityStyles).toContain('border-inline-start:3px double Highlight');
});

test('odd metrics center the orphan and governed scroll owners share accessible scrollbar tokens', () => {
  expect(collectionStyles).toContain(':last-child:nth-child(odd){grid-column:1/-1;width:50%;justify-self:center}');
  expect(scrollbarStyles).toContain('::-webkit-scrollbar-thumb:hover');
  expect(scrollbarStyles).toContain('scrollbar-color:var(--soma-scrollbar-thumb) var(--soma-scrollbar-track)');
  expect(scrollbarStyles).toContain('@media(forced-colors:active)');
  expect(tokenStyles).toContain('--soma-scrollbar-size:12px');
});
