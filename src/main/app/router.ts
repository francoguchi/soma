export type ReturnState = Readonly<{filters: Record<string, string>; activeId: string | null; selectedIds: readonly string[]; pane: string | null; tab: string | null; scrollTop: number; focusToken: string | null}>;
export type Route = Readonly<{path: string; capability: string; title: string}>;
import {workspaces, systemDestinations} from './workspaces/registry';
export const routes: readonly Route[] = [...workspaces, ...systemDestinations];
export function resolveRoute(path: string, registry: readonly Route[] = routes): Route | null {return registry.find(route => route.path === path) ?? null;}
export class Navigation {
  constructor(private capture: () => ReturnState | null) {}
  open(path: string) {
    if (!resolveRoute(path)) throw new Error('Unknown SOMA route.');
    history.replaceState({context: this.capture()}, '', location.href);
    history.pushState({context: null}, '', path);
    dispatchEvent(new PopStateEvent('popstate', {state: {context: null}}));
  }
}
