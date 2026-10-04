import {expect, test} from 'vitest';
import entry from '../styles/soma.css?raw';
const library = import.meta.glob('../styles/**/*.css', {query: '?raw', import: 'default', eager: true}) as Record<string, string>;

test('stable style entry exposes ordered layers and every shared primitive', () => {
  expect(entry).toContain('@layer reset, tokens, base, primitives, components, utilities, features;');
  for (const name of ['actions', 'panes', 'collections', 'forms', 'feedback', 'scrollbars', 'status']) {
    expect(entry).toContain(`./primitives/${name}.css`);
  }
});

test('palette ownership and semantic token names do not drift into shared primitives', () => {
  for (const [path, source] of Object.entries(library)) {
    if (!path.endsWith('/tokens.css')) expect(source, path).not.toMatch(/#[0-9a-f]{3,8}\b/i);
    for (const name of source.matchAll(/var\((--[a-z-]+)/g)) expect(name[1], path).toMatch(/^--soma-/);
    if (!path.endsWith('/reset.css') && !path.endsWith('/utilities.css')) expect(source, path).not.toContain('!important');
  }
});
