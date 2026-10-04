import type {BootstrapV1} from '../../shared/api/generated/contracts';

// Product navigation authority. Capability registration never adds labels.
export const workspaces = [
  {path: '/', capability: 'overview', title: 'Overview'},
  {path: '/tickets', capability: 'tickets', title: 'Tickets'},
  {path: '/objectives', capability: 'objectives', title: 'Objectives'},
  {path: '/inventory', capability: 'inventory', title: 'Inventory'},
  {path: '/infrastructure', capability: 'infrastructure', title: 'Infrastructure'},
  {path: '/settings', capability: 'settings', title: 'Settings'},
] as const;
export const systemDestinations = [
  {path: '/system/diagnostics', capability: 'foundation.diagnostics', title: 'Diagnostics'},
] as const;
export function workspaceState(capability: string, capabilities: BootstrapV1['capabilities']) {
  return capabilities.find(item => item.id === capability)?.state ?? 'unavailable';
}
