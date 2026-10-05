export type ReturnState = Readonly<{filters: Record<string, string>; activeId: string | null; selectedIds: readonly string[]; pane: string | null; tab: string | null; scrollTop: number; focusToken: string | null}>;
export type Route = Readonly<{path: string; capability: string; title: string}>;
import {workspaces, systemDestinations} from './workspaces/registry';
import {requestNavigation} from '../shared/interactions/use-working-intent';
export const routes: readonly Route[] = [...workspaces, ...systemDestinations];
export function resolveRoute(path: string, registry: readonly Route[] = routes): Route | null {
  const declared = registry.find(route => route.path === path);
  if (declared) return declared;
  if (registry === routes && /^\/settings\/(?:profile|preferences|reference-data(?:\/(?:customer_organization|contact|dispatch_location)(?:\/(?:new|[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}))?)?)$/u.test(path)) return {path, capability: 'settings', title: 'Settings'};
  return null;
}
export class Navigation {
  constructor(private capture: () => ReturnState | null) {}
  open(path: string) {
    if (!resolveRoute(path)) throw new Error('Unknown SOMA route.');
    requestNavigation(path, () => {
      history.replaceState({context: this.capture()}, '', location.href);
      history.pushState({context: null}, '', path);
      dispatchEvent(new PopStateEvent('popstate', {state: {context: null, authorized: true}}));
    });
  }
}
