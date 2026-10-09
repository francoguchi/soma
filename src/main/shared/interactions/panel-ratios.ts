export type PanelRatios = Readonly<{upper: number; left: number}>;
export const defaultRatios: PanelRatios = {upper: 40, left: 50};
// Session presentation only. No durable storage or business authority.
const session = new Map<string, PanelRatios>();
export const readRatios = (key: string): PanelRatios => session.get(key) ?? defaultRatios;
export function clampRatio(value: number, extent: number, minimum: number) {
  const bound = Math.min(45, Math.max(25, minimum / Math.max(extent, 1) * 100));
  return Math.min(100 - bound, Math.max(bound, value));
}
export function rememberRatios(key: string, ratios: PanelRatios) {
  session.set(key, ratios);
}
